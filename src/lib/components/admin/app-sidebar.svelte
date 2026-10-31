<script lang="ts">
  import HeartPulseIcon from "@lucide/svelte/icons/heart-pulse";
  import { resolve } from "$app/paths";
  import { page } from "$app/state";
  import { activeNavItem, NAV_GROUPS } from "#lib/admin/nav.js";
  import type { AdminUser } from "#lib/admin/types.js";
  import * as Sidebar from "#lib/components/ui/sidebar/index.js";
  import NavUser from "./nav-user.svelte";

  let { user }: { user: AdminUser } = $props();

  const sidebar = Sidebar.useSidebar();
  const active = $derived(activeNavItem(page.url.pathname));
  const groups = $derived(
    NAV_GROUPS.map((group) => ({
      ...group,
      items: group.items.filter((item) => !item.adminOnly || user.isAdmin)
    })).filter((group) => group.items.length > 0)
  );

  // On phones the sidebar is a sheet; close it once a page is chosen
  const closeOnMobile = () => sidebar.setOpenMobile(false);
</script>

<Sidebar.Root collapsible="icon">
  <Sidebar.Header>
    <Sidebar.Menu>
      <Sidebar.MenuItem>
        <Sidebar.MenuButton size="lg">
          {#snippet child({ props })}
            <a href={resolve("admin")} onclick={closeOnMobile} {...props}>
              <div
                class="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground"
              >
                <HeartPulseIcon />
              </div>
              <div class="grid flex-1 text-left text-sm leading-tight">
                <span class="truncate font-medium">Medtour</span>
                <span class="truncate text-xs text-muted-foreground">Staff admin</span>
              </div>
            </a>
          {/snippet}
        </Sidebar.MenuButton>
      </Sidebar.MenuItem>
    </Sidebar.Menu>
  </Sidebar.Header>

  <Sidebar.Content>
    {#each groups as group (group.label)}
      <Sidebar.Group>
        <Sidebar.GroupLabel>{group.label}</Sidebar.GroupLabel>
        <Sidebar.Menu>
          {#each group.items as item (item.path)}
            {@const isActive = item === active}
            <Sidebar.MenuItem>
              <Sidebar.MenuButton {isActive} tooltipContent={item.title}>
                {#snippet child({ props })}
                  <a
                    href={resolve(item.path)}
                    aria-current={isActive ? "page" : undefined}
                    onclick={closeOnMobile}
                    {...props}
                  >
                    <item.icon />
                    <span>{item.title}</span>
                  </a>
                {/snippet}
              </Sidebar.MenuButton>
            </Sidebar.MenuItem>
          {/each}
        </Sidebar.Menu>
      </Sidebar.Group>
    {/each}
  </Sidebar.Content>

  <Sidebar.Footer>
    <NavUser {user} />
  </Sidebar.Footer>
  <Sidebar.Rail />
</Sidebar.Root>
