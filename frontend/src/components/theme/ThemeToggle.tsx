import { Sun, Moon, Monitor } from 'lucide-react';
import { useTheme } from './ThemeProvider';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';

const themeOrder = ['light', 'dark', 'system'] as const;
const themeLabel = { light: 'Light', dark: 'Dark', system: 'System' } as const;
const themeIcon = { light: Sun, dark: Moon, system: Monitor } as const;

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const Icon = themeIcon[theme];
  const nextTheme = themeOrder[(themeOrder.indexOf(theme) + 1) % themeOrder.length];

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          onClick={() => setTheme(nextTheme)}
          className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
          aria-label={`Switch to ${themeLabel[nextTheme]} theme`}
        >
          <Icon className="size-4" />
        </button>
      </TooltipTrigger>
      <TooltipContent side="bottom">
        <p>{themeLabel[theme]} theme (click to switch)</p>
      </TooltipContent>
    </Tooltip>
  );
}
