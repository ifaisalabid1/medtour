import type { Component } from "svelte";
import type { Path } from "$app/types";
import LayoutDashboardIcon from "@lucide/svelte/icons/layout-dashboard";

export interface NavItem {
  title: string;
  /** Pathname without the leading slash, as `resolve()` expects. */
  path: Path;
  icon: Component;
  /** Only shown to users with the `admin` role. */
  adminOnly?: boolean;
}

export interface NavGroup {
  label: string;
  items: NavItem[];
}

/** Sidebar navigation. Each admin step adds its pages here. */
export const NAV_GROUPS: NavGroup[] = [
  {
    label: "Overview",
    items: [{ title: "Dashboard", path: "admin", icon: LayoutDashboardIcon }]
  }
];

/** The nav item a pathname belongs to: the longest matching prefix wins. */
export function activeNavItem(pathname: string): NavItem | undefined {
  const items = NAV_GROUPS.flatMap((group) => group.items);
  return items
    .filter((item) => pathname === `/${item.path}` || pathname.startsWith(`/${item.path}/`))
    .sort((a, b) => b.path.length - a.path.length)[0];
}
