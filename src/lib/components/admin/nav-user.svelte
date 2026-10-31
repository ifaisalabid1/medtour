<script lang="ts">
  import ChevronsUpDownIcon from "@lucide/svelte/icons/chevrons-up-down";
  import LogOutIcon from "@lucide/svelte/icons/log-out";
  import { toast } from "svelte-sonner";
  import { goto } from "$app/navigation";
  import { resolve } from "$app/paths";
  import type { AdminUser } from "#lib/admin/types.js";
  import { authClient } from "#lib/auth-client.js";
  import * as Avatar from "#lib/components/ui/avatar/index.js";
  import { Badge } from "#lib/components/ui/badge/index.js";
  import * as DropdownMenu from "#lib/components/ui/dropdown-menu/index.js";
  import * as Sidebar from "#lib/components/ui/sidebar/index.js";

  let { user }: { user: AdminUser } = $props();

  const sidebar = Sidebar.useSidebar();

  const initials = $derived(
    user.name
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((word) => word[0]!.toUpperCase())
      .join("")
  );

  async function signOut() {
    const { error } = await authClient.signOut();
    if (error) {
      toast.error("Could not sign out. Try again.");
      return;
    }
    await goto(resolve("/admin/login"), { refreshAll: true });
  }
</script>

{#snippet identity()}
  <Avatar.Root class="size-8 rounded-lg">
    <Avatar.Fallback class="rounded-lg">{initials}</Avatar.Fallback>
  </Avatar.Root>
  <div class="grid flex-1 text-left text-sm leading-tight">
    <span class="truncate font-medium">{user.name}</span>
    <span class="truncate text-xs text-muted-foreground">{user.email}</span>
  </div>
{/snippet}

<Sidebar.Menu>
  <Sidebar.MenuItem>
    <DropdownMenu.Root>
      <DropdownMenu.Trigger>
        {#snippet child({ props })}
          <Sidebar.MenuButton size="lg" class="data-open:bg-sidebar-accent" {...props}>
            {@render identity()}
            <ChevronsUpDownIcon class="ml-auto" />
          </Sidebar.MenuButton>
        {/snippet}
      </DropdownMenu.Trigger>
      <DropdownMenu.Content
        class="min-w-56 rounded-lg"
        side={sidebar.isMobile ? "bottom" : "right"}
        align="end"
        sideOffset={4}
      >
        <DropdownMenu.Label class="p-0 font-normal">
          <div class="flex items-center gap-2 px-1 py-1.5">
            {@render identity()}
          </div>
        </DropdownMenu.Label>
        <DropdownMenu.Group>
          <DropdownMenu.Item disabled>
            Role
            <Badge variant="secondary" class="ml-auto">{user.isAdmin ? "Admin" : "Staff"}</Badge>
          </DropdownMenu.Item>
        </DropdownMenu.Group>
        <DropdownMenu.Separator />
        <DropdownMenu.Group>
          <DropdownMenu.Item onSelect={signOut}>
            <LogOutIcon />
            Sign out
          </DropdownMenu.Item>
        </DropdownMenu.Group>
      </DropdownMenu.Content>
    </DropdownMenu.Root>
  </Sidebar.MenuItem>
</Sidebar.Menu>
