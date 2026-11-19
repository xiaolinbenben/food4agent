#!/usr/bin/env python3
"""broker-card: Generate listing cards and auto-publish (Step 4).

Generates platform-adapted listing previews, collects schedule+fuse settings,
and auto-publishes on user confirmation.
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from broker_core.state_manager import ListingsStore, ListingState
from broker_core.platform_client import get_client, ListingDraft

PLATFORM_STYLES = {
    "xianyu": {"name": "闲鱼 Xianyu", "title_max": 30, "tone": "casual, authentic, first-person"},
    "zhuanzhuan": {"name": "转转 Zhuanzhuan", "title_max": 40, "tone": "semi-formal, inspection-report"},
    "ebay": {"name": "eBay", "title_max": 80, "tone": "professional, keyword-dense"},
    "depop": {"name": "Depop", "title_max": 60, "tone": "lifestyle, aesthetic-focused"},
}


def generate_card(product: dict, price: float, platform: str) -> str:
    """Generate a markdown listing card for the specified platform."""
    style = PLATFORM_STYLES.get(platform, PLATFORM_STYLES["xianyu"])
    brand = product.get("brand", "")
    name = product.get("product_name", "")
    condition = product.get("condition_grade", "")
    condition_detail = product.get("condition_detail", "")
    color = product.get("color", "")
    category = product.get("category_path", "")
    flaws = product.get("flaws", [])
    features = product.get("notable_features", [])

    # Platform-specific title
    if platform == "xianyu":
        cond_cn = {"A": "全新", "B": "九成新", "C": "八成新", "D": "六成新", "E": "故障"}
        title = f"{brand} {name} {color} {cond_cn.get(condition, '')}"[:style["title_max"]]
    elif platform == "ebay":
        title = f"{brand} {product.get('model', '')} {name} {color} {condition}"[:style["title_max"]]
    else:
        title = f"{brand} {name} {color}"[:style["title_max"]]

    # Platform-specific description
    if platform == "xianyu":
        desc_lines = [f"{brand} {name}，{color}色。成色：{condition_detail}。",
                      f"瑕疵：{'；'.join(flaws)}。" if flaws else "",
                      "诚心出，爽快可小刀，有问题随意问。"]
    elif platform == "zhuanzhuan":
        desc_lines = [f"品牌：{brand}", f"品名：{name}", f"成色：{condition_detail}",
                      f"瑕疵：{'；'.join(flaws)}" if flaws else ""]
    elif platform == "ebay":
        desc_lines = [f"{brand} {name} in {color}. Condition: {condition_detail}.",
                      f"Note: {'; '.join(flaws)}." if flaws else "",
                      "Ships from China. Check photos for full condition details."]
    elif platform == "depop":
        desc_lines = [f"{brand} {name} in {color} ✨", f"Condition: {condition_detail}",
                      f"{' | '.join(features)}" if features else ""]
    else:
        desc_lines = [f"{brand} {name}. {condition_detail}."]
    description = "\n\n".join(l for l in desc_lines if l)

    # Platform-specific tags
    if platform == "depop":
        tags = " ".join(f"#{t}" for t in [brand, name, color, condition] if t)
    else:
        tags = " ".join(f"#{t}" for t in [brand, name, color, condition, "闲置"] if t)

    card = f"""## 🛍️ Listing Card — {style['name']}

```
┌─────────────────────────────────────┐
│ 🛍️  {style['name']} 上架卡片
├─────────────────────────────────────┤
│  📝 标题: {title}
│  📂 分类: {category}
│  💰 价格: ¥{price:,.2f}
│  ⚠️  成色: Grade {condition} — {condition_detail[:40]}
│  📋 描述: {description[:80].replace(chr(10), ' ')}...
│  🏷️  标签: {tags[:50]}
└─────────────────────────────────────┘
```

**Edit or confirm to publish?** Also set:
- Repricing interval (default 7 days)
- Price shield (floor price)
"""
    return card


def publish_listing(item_id: str, platform: str) -> Optional[str]:
    """Publish a listing to the platform using stored session."""
    store = ListingsStore()
    state = store.get(item_id)
    if state is None:
        print(f"❌ Listing {item_id} not found")
        return None

    client = get_client(platform)
    if client is None:
        print(f"❌ No valid session for {platform}. Run broker-auth first.")
        return None

    draft = ListingDraft(
        title=f"{state.product_brand} {state.product_name}",
        description=f"{state.product_brand} {state.product_name}. "
                    f"Condition: {state.product_condition_detail}. "
                    f"Price: ¥{state.current_price}.",
        price=state.current_price,
        category=state.product_category,
        tags=[state.product_brand, state.product_name, state.product_color, state.product_condition_grade],
        condition_grade=state.product_condition_grade,
    )

    url = client.publish(draft)
    if url:
        state.platform_urls[platform] = url
        if platform not in state.platforms:
            state.platforms.append(platform)
        store.update(state)
        print(f"✅ Published to {platform}: {url}")
    else:
        print(f"⚠️  Publish to {platform} may have failed. Check the platform manually.")
    return url


def main():
    p = argparse.ArgumentParser(description="broker-card — Step 4: Listing Cards & Publish")
    p.add_argument("--item-id", help="Listing item ID")
    p.add_argument("--product", help="Product JSON (for card generation)")
    p.add_argument("--price", type=float, help="Listing price")
    p.add_argument("--platform", help="Single platform for card preview")
    p.add_argument("--platforms", help="Comma-separated platforms for publishing")
    p.add_argument("--action", default="generate", choices=["generate", "publish", "status"])
    args = p.parse_args()

    store = ListingsStore()

    if args.action == "generate":
        if not args.product or not args.price:
            print("--product and --price required for card generation")
            return
        product = json.loads(args.product)
        platform = args.platform or "xianyu"
        card = generate_card(product, args.price, platform)
        print(card)

    elif args.action == "publish":
        if not args.item_id:
            print("--item-id required for publish")
            return
        platforms = [x.strip() for x in (args.platforms or "xianyu").split(",")]
        for plat in platforms:
            publish_listing(args.item_id, plat)

    elif args.action == "status":
        if args.item_id:
            state = store.get(args.item_id)
            if state:
                print(json.dumps({
                    "item_id": state.item_id, "status": state.status,
                    "platforms": state.platforms, "urls": state.platform_urls,
                    "current_price": state.current_price, "fuse_price": state.fuse_price,
                }, indent=2, ensure_ascii=False))
            else:
                print(f"Listing {args.item_id} not found")
        else:
            active = store.list_active()
            print(f"Active listings: {len(active)}")
            for s in active:
                print(f"  {s.item_id}: {s.product_brand} {s.product_name} — ¥{s.current_price} [{s.status}]")


if __name__ == "__main__":
    main()
