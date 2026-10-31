<script lang="ts">
  import { Toaster } from "#lib/components/ui/sonner/index.js";
  import type { LayoutProps } from "./$types";

  let { children }: LayoutProps = $props();
</script>

<svelte:head>
  <meta name="robots" content="noindex, nofollow" />
</svelte:head>

<Toaster />
{@render children()}
