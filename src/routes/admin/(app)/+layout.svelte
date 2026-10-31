<script lang="ts">
  import { page } from "$app/state";
  import { activeNavItem } from "#lib/admin/nav.js";
  import AppSidebar from "#lib/components/admin/app-sidebar.svelte";
  import { Separator } from "#lib/components/ui/separator/index.js";
  import * as Sidebar from "#lib/components/ui/sidebar/index.js";
  import type { LayoutProps } from "./$types";

  let { data, children }: LayoutProps = $props();

  const section = $derived(activeNavItem(page.url.pathname));
</script>

<Sidebar.Provider open={data.sidebarOpen}>
  <AppSidebar user={data.user} />
  <Sidebar.Inset>
    <header class="flex h-14 shrink-0 items-center gap-2 border-b px-4">
      <Sidebar.Trigger class="-ml-1" />
      <Separator orientation="vertical" class="mr-2 data-vertical:h-4 data-vertical:self-center" />
      <span class="text-sm font-medium">{section?.title ?? "Admin"}</span>
    </header>
    <main class="flex flex-1 flex-col gap-6 p-4 md:p-6">
      {@render children()}
    </main>
  </Sidebar.Inset>
</Sidebar.Provider>
