param(
  [Parameter(Mandatory = $true)]
  [string]$RawProductJson,

  [string]$OutputPath
)

$ErrorActionPreference = "Stop"

function Read-JsonFile {
  param([string]$Path)
  return Get-Content -Raw -Encoding UTF8 $Path | ConvertFrom-Json
}

function Write-JsonFile {
  param(
    [string]$Path,
    [object]$Value
  )

  $json = $Value | ConvertTo-Json -Depth 100
  [System.IO.File]::WriteAllText($Path, ($json -join [Environment]::NewLine) + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
}

function Get-TextOrEmpty {
  param([object]$Value)
  if ($null -eq $Value) { return "" }
  return [string]$Value
}

function Get-UniqueStringArray {
  param([object[]]$Values)

  $result = [System.Collections.Generic.List[string]]::new()
  foreach ($value in $Values) {
    if ($null -eq $value) { continue }

    if ($value -is [System.Collections.IEnumerable] -and -not ($value -is [string])) {
      foreach ($nested in $value) {
        $text = ([string]$nested).Trim()
        if (-not $text) { continue }
        if (-not $result.Contains($text)) { $result.Add($text) }
      }
      continue
    }

    $text = ([string]$value).Trim()
    if (-not $text) { continue }
    if (-not $result.Contains($text)) { $result.Add($text) }
  }

  return $result.ToArray()
}

function Get-SkuPurchaseRows {
  param([object]$Raw)

  $rows = [System.Collections.Generic.List[object]]::new()
  foreach ($item in @($Raw.structured.sku.items)) {
    if ($null -eq $item) { continue }
    $priceCny = $item.price_cny
    if ($null -eq $priceCny -or "$priceCny" -eq "") { continue }

    $priceDecimal = [decimal]$priceCny
    $base = ($priceDecimal * 8) / 6.5
    $sale = [math]::Floor([double]$base).ToString() + ".99"

    $rows.Add([pscustomobject]@{
      sku_text = Get-TextOrEmpty $item.sku_text
      spec_id = Get-TextOrEmpty $item.spec_id
      color = Get-TextOrEmpty $item.color
      size = Get-TextOrEmpty $item.size
      purchase_price_cny = [string]$priceDecimal
      derived_sale_price_usd = $sale
    })
  }

  return $rows.ToArray()
}

function Get-VariantSourceRows {
  param([object]$Raw)

  $rows = [System.Collections.Generic.List[object]]::new()
  foreach ($item in @($Raw.structured.sku.items)) {
    if ($null -eq $item) { continue }
    $rows.Add([pscustomobject]@{
      sku_text = Get-TextOrEmpty $item.sku_text
      color = Get-TextOrEmpty $item.color
      size = Get-TextOrEmpty $item.size
      spec_id = Get-TextOrEmpty $item.spec_id
    })
  }

  return $rows.ToArray()
}

$rawPath = (Resolve-Path -LiteralPath $RawProductJson).Path
$raw = Read-JsonFile -Path $rawPath

if (-not $OutputPath) {
  $OutputPath = Join-Path (Split-Path -Parent $rawPath) "product-context.json"
}

$context = [ordered]@{
  source = [ordered]@{
    offer_id = Get-TextOrEmpty $raw.source.offer_id
    url = Get-TextOrEmpty $raw.source.url
    page_title = Get-TextOrEmpty $raw.source.page_title
  }
  title = [ordered]@{
    primary = Get-TextOrEmpty $raw.structured.title.primary
    candidates = Get-UniqueStringArray @($raw.structured.title.candidates)
  }
  description = [ordered]@{
    text = Get-TextOrEmpty $raw.structured.description.text
  }
  attributes = [ordered]@{
    items = @($raw.structured.attributes.items)
  }
  variants = [ordered]@{
    source_rows = @(Get-VariantSourceRows -Raw $raw)
  }
  pricing = [ordered]@{
    sku_purchase_prices_cny = @((Get-SkuPurchaseRows -Raw $raw) | ForEach-Object { $_.purchase_price_cny })
    derived_sale_prices_usd = @((Get-SkuPurchaseRows -Raw $raw) | ForEach-Object { $_.derived_sale_price_usd })
    sku_rows = @(Get-SkuPurchaseRows -Raw $raw)
  }
  images = [ordered]@{
    main_images = Get-UniqueStringArray @($raw.structured.images.main_images)
    sku_images = Get-UniqueStringArray @($raw.structured.images.sku_images)
    detail_images = Get-UniqueStringArray @($raw.structured.images.detail_images)
    candidates = Get-UniqueStringArray @($raw.structured.images.candidates)
  }
  size_chart = [ordered]@{
    image_urls = Get-UniqueStringArray @($raw.structured.shein_required_fields.size_chart.image_urls)
  }
  quality = [ordered]@{
    missing_fields = @($raw.quality.missing_fields)
  }
  raw_text_excerpt = (Get-TextOrEmpty $raw.raw.text)
}

if ($context.raw_text_excerpt.Length -gt 4000) {
  $context.raw_text_excerpt = $context.raw_text_excerpt.Substring(0, 4000)
}

Write-JsonFile -Path $OutputPath -Value $context
Write-Output $OutputPath
