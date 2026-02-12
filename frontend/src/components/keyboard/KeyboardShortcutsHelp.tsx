import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { useUIStore } from '@/stores/ui-store';
import { SHORTCUTS, SCOPE_LABELS, type ShortcutDef } from '@/lib/shortcuts-config';

function Kbd({ children }: { children: string }) {
  return (
    <kbd className="inline-flex h-5 min-w-5 items-center justify-center rounded border border-border bg-muted px-1.5 text-[11px] font-mono text-muted-foreground">
      {children}
    </kbd>
  );
}

function ShortcutRow({ shortcut }: { shortcut: ShortcutDef }) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-sm">{shortcut.description}</span>
      <span className="ml-4 flex shrink-0 items-center gap-1">
        <Kbd>{shortcut.label}</Kbd>
      </span>
    </div>
  );
}

export function KeyboardShortcutsHelp() {
  const open = useUIStore((s) => s.helpDialogOpen);
  const setOpen = useUIStore((s) => s.setHelpDialogOpen);

  const grouped = new Map<string, ShortcutDef[]>();
  for (const shortcut of Object.values(SHORTCUTS)) {
    const existing = grouped.get(shortcut.scope) ?? [];
    existing.push(shortcut);
    grouped.set(shortcut.scope, existing);
  }

  const scopeOrder = ['global', 'entry-list', 'entry-action', 'sidebar'] as const;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="max-h-[80vh] overflow-y-auto sm:max-w-md">
        <DialogHeader>
          <DialogTitle>快捷键</DialogTitle>
          <DialogDescription>键盘快捷键一览</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          {scopeOrder.map((scope) => {
            const shortcuts = grouped.get(scope);
            if (!shortcuts) return null;
            return (
              <div key={scope}>
                <h3 className="mb-1 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  {SCOPE_LABELS[scope]}
                </h3>
                <div className="divide-y divide-border/50">
                  {shortcuts.map((s, i) => (
                    <ShortcutRow key={i} shortcut={s} />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </DialogContent>
    </Dialog>
  );
}
