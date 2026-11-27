import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";

const copyModeKey = "food4agent.skill-copy-mode";
const copyModeEvent = "food4agent.skill-copy-mode";

const copyModes = {
  url: { label: "复制地址", text: (url: string) => url },
  cli: { label: "复制安装命令", text: (url: string) => `npx skills add ${url}` },
  prompt: { label: "复制安装口令", text: (url: string) => `帮我安装 ${url} 这个技能。` },
} as const;

const copyModeOrder = ["url", "cli", "prompt"] as const;

type CopyMode = (typeof copyModeOrder)[number];

function readCopyMode(): CopyMode {
  const value = localStorage.getItem(copyModeKey);
  if (value === "url" || value === "cli" || value === "prompt") return value;
  return "url";
}

function writeCopyMode(mode: CopyMode) {
  localStorage.setItem(copyModeKey, mode);
  window.dispatchEvent(new Event(copyModeEvent));
}

function useCopyMode() {
  const [mode, setMode] = useState<CopyMode>(readCopyMode);
  useEffect(() => {
    const sync = () => setMode(readCopyMode());
    window.addEventListener(copyModeEvent, sync);
    return () => window.removeEventListener(copyModeEvent, sync);
  }, []);
  return mode;
}

export function SkillCopyButton({ url, size, onCopy }: { url: string; size?: "sm"; onCopy?: (value: string) => boolean | void | Promise<boolean | void> }) {
  const mode = useCopyMode();
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  async function choose(next: CopyMode) {
    const value = copyModes[next].text(url);
    if (onCopy) {
      const result = await onCopy(value);
      if (result === false) return;
    } else {
      await navigator.clipboard.writeText(value);
    }
    writeCopyMode(next);
    setCopied(true);
  }

  return (
    <div className="relative shrink-0" onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)}>
      {open && (
        <div className="absolute bottom-full right-0 z-30 pb-2">
          <div className="min-w-max border-3 border-foreground bg-background shadow-[4px_4px_0px_hsl(var(--shadow-color))]">
            {copyModeOrder.map((id) => (
              <button
                key={id}
                type="button"
                className={`block w-full border-b-3 border-foreground px-3 py-2 text-left text-xs font-bold uppercase tracking-wide last:border-b-0 ${id === mode ? "bg-primary text-primary-foreground" : "bg-background hover:bg-muted"}`}
                onClick={() => void choose(id)}
              >
                {copyModes[id].label}
              </button>
            ))}
          </div>
        </div>
      )}
      <Button size={size} onClick={() => void choose(mode)}>{copied ? "已复制" : "复制"}</Button>
    </div>
  );
}
