<script lang="ts">
  import type { PageProps } from "./$types";

  let { data }: PageProps = $props();
</script>

<h1>Admin</h1>
<p>Signed in as {data.user?.name} ({data.user?.role})</p>
