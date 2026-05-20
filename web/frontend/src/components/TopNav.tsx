import type { LucideIcon } from 'lucide-react';
import type { PageKey } from '../types';

type NavItem = {
  key: PageKey;
  label: string;
  icon: LucideIcon;
};

export function TopNav({
  items,
  active,
  onChange,
}: {
  items: NavItem[];
  active: PageKey;
  onChange: (key: PageKey) => void;
}) {
  return (
    <header className="top-nav">
      <button className="brand" onClick={() => onChange('dashboard')} type="button">
        <span className="brand-mark" />
        <span>AITrend</span>
      </button>
      <nav className="nav-links">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <button
              className={`nav-item ${active === item.key ? 'active' : ''}`}
              key={item.key}
              onClick={() => onChange(item.key)}
              type="button"
            >
              <Icon size={16} />
              {item.label}
            </button>
          );
        })}
      </nav>
    </header>
  );
}
