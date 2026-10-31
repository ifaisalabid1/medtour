<script lang="ts">
  import { LEAD_STATUS_LABELS } from "#lib/admin/labels.js";
  import PageHeader from "#lib/components/admin/page-header.svelte";
  import * as Card from "#lib/components/ui/card/index.js";
  import { LEAD_STATUSES, type LeadStatus } from "#lib/domain/leads.js";
  import type { PageProps } from "./$types";

  let { data }: PageProps = $props();

  const OPEN_STATUSES: LeadStatus[] = [
    "contacted",
    "awaiting_documents",
    "under_review",
    "quote_sent"
  ];

  const stats = $derived(data.stats);
  const openLeads = $derived(
    OPEN_STATUSES.reduce((sum, status) => sum + stats.leadsByStatus[status], 0)
  );
  const directory = $derived([
    { title: "Hospitals", counts: stats.hospitals },
    { title: "Doctors", counts: stats.doctors },
    { title: "Procedures", counts: stats.procedures }
  ]);
</script>

<PageHeader title="Dashboard" description="Welcome back, {data.user.name}." />

<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
  <Card.Root>
    <Card.Header>
      <Card.Description>New enquiries</Card.Description>
      <Card.Title class="text-3xl tabular-nums">{stats.leadsByStatus.new}</Card.Title>
    </Card.Header>
    <Card.Footer class="text-sm text-muted-foreground">Waiting for a first reply</Card.Footer>
  </Card.Root>
  <Card.Root>
    <Card.Header>
      <Card.Description>In progress</Card.Description>
      <Card.Title class="text-3xl tabular-nums">{openLeads}</Card.Title>
    </Card.Header>
    <Card.Footer class="text-sm text-muted-foreground">Contacted, reviewing or quoted</Card.Footer>
  </Card.Root>
  <Card.Root>
    <Card.Header>
      <Card.Description>Last 7 days</Card.Description>
      <Card.Title class="text-3xl tabular-nums">{stats.leadsLast7Days}</Card.Title>
    </Card.Header>
    <Card.Footer class="text-sm text-muted-foreground">Enquiries received</Card.Footer>
  </Card.Root>
</div>

<div class="grid gap-4 lg:grid-cols-2">
  <Card.Root>
    <Card.Header>
      <Card.Title>Enquiries by status</Card.Title>
      <Card.Description>All enquiries received so far</Card.Description>
    </Card.Header>
    <Card.Content>
      <dl class="flex flex-col gap-2 text-sm">
        {#each LEAD_STATUSES as status (status)}
          <div class="flex items-center justify-between">
            <dt class="text-muted-foreground">{LEAD_STATUS_LABELS[status]}</dt>
            <dd class="font-medium tabular-nums">{stats.leadsByStatus[status]}</dd>
          </div>
        {/each}
      </dl>
    </Card.Content>
  </Card.Root>

  <Card.Root>
    <Card.Header>
      <Card.Title>Directory</Card.Title>
      <Card.Description>Published profiles are visible on the public site</Card.Description>
    </Card.Header>
    <Card.Content>
      <dl class="flex flex-col gap-2 text-sm">
        {#each directory as entry (entry.title)}
          <div class="flex items-center justify-between">
            <dt class="text-muted-foreground">{entry.title}</dt>
            <dd class="tabular-nums">
              <span class="font-medium">{entry.counts.published}</span> published ·
              {entry.counts.draft} draft
            </dd>
          </div>
        {/each}
      </dl>
    </Card.Content>
  </Card.Root>
</div>
