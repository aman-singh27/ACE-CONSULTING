import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { getCompanies } from "../../services/api/companies";
import { getSyncHistory, setupHubSpotProperties, triggerHubSpotSync, saveHubSpotAPIKey } from "../../services/api/hubspot";
import type { SyncHistoryEntry } from "../../services/api/hubspot";
import { HubSpotSyncPanel } from "../../components/dashboard/HubSpotSyncPanel";
import { KpiCard } from "../../components/ui/KpiCard";
import { Badge } from "../../components/ui/Badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/Table";
import { Button } from "../../components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/Card";
import {
  Link2,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Search,
  ExternalLink,
  CircleDot,
  ArrowRight,
  Loader2,
  Zap
} from "lucide-react";
import { relativeTime } from "../../utils/relativeTime";

export function HubSpotPage() {
  const [activeTab, setActiveTab] = useState<'overview' | 'companies' | 'history' | 'setup'>('overview');

  return (
    <div className="flex flex-col h-full w-full">
      {/* Header */}
      <div className="mb-8 shrink-0">
        <div className="flex justify-between items-end">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-text-primary">HubSpot CRM</h1>
            <p className="text-text-secondary mt-1">Sync hiring intelligence to your CRM</p>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#FF7A59]/10 border border-[#FF7A59]/20">
            <Link2 className="h-4 w-4" style={{ color: '#FF7A59' }} />
            <span className="text-sm font-medium" style={{ color: '#FF7A59' }}>HubSpot</span>
          </div>
        </div>
      </div>

      {/* Tab Bar */}
      <div className="flex gap-1 mb-6 bg-bg-elevated p-1 rounded-lg w-fit">
        {[
          { id: 'overview', label: 'Overview' },
          { id: 'companies', label: 'Companies' },
          { id: 'history', label: 'History' },
          { id: 'setup', label: 'Setup' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-4 py-2 text-sm rounded-md transition-all cursor-pointer ${
              activeTab === tab.id
                ? 'bg-bg-surface text-text-primary font-medium shadow-sm'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-grow min-h-0">
        {activeTab === 'overview' && <HubSpotOverviewTab />}
        {activeTab === 'companies' && <HubSpotCompaniesTab />}
        {activeTab === 'history' && <HubSpotHistoryTab />}
        {activeTab === 'setup' && <HubSpotSetupTab onSetupComplete={() => setActiveTab('overview')} />}
      </div>
    </div>
  );
}

function HubSpotOverviewTab() {
  const { data: companiesData, refetch: refetchCompanies } = useQuery({
    queryKey: ["companies", { limit: 1000 }],
    queryFn: () => getCompanies({ limit: 1000 }),
  });

  const allCompanies = companiesData?.items ?? [];
  const syncedCount = allCompanies.filter((c: any) => c.hubspot_company_id).length;
  const unsyncedCount = allCompanies.length - syncedCount;
  const dealCount = allCompanies.filter((c: any) => c.hubspot_deal_id).length;
  const syncRate = allCompanies.length > 0 ? Math.round((syncedCount / allCompanies.length) * 100) : 0;

  return (
    <div className="space-y-6">
      <HubSpotSyncPanel onSyncComplete={() => refetchCompanies()} />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard label="Companies synced" metric={syncedCount} />
        <KpiCard label="Pending sync" metric={unsyncedCount} />
        <KpiCard label="Deals created" metric={dealCount} />
        <KpiCard label="Sync coverage" metric={`${syncRate}%`} />
      </div>
    </div>
  );
}

function HubSpotCompaniesTab() {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<'all' | 'synced' | 'unsynced'>('all');

  const { data: companiesData, isLoading } = useQuery({
    queryKey: ["companies", { limit: 1000 }],
    queryFn: () => getCompanies({ limit: 1000 }),
  });

  const allCompanies = companiesData?.items ?? [];

  const filtered = allCompanies
    .filter((c: any) => {
      if (filter === 'synced') return !!c.hubspot_company_id;
      if (filter === 'unsynced') return !c.hubspot_company_id;
      return true;
    })
    .filter((c: any) => c.company_name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex gap-3 items-center flex-wrap">
        <div className="relative max-w-xs">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-text-muted" />
          <input
            type="text"
            placeholder="Search companies..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full border border-border-default rounded-md bg-bg-base text-text-primary pl-10 py-2 text-sm"
          />
        </div>

        {[
          { id: 'all', label: 'All' },
          { id: 'synced', label: 'Synced' },
          { id: 'unsynced', label: 'Not synced' },
        ].map((filterOption) => (
          <button
            key={filterOption.id}
            onClick={() => setFilter(filterOption.id as any)}
            className={`px-3 py-1.5 text-sm rounded-md border cursor-pointer transition-colors ${
              filter === filterOption.id
                ? 'bg-accent-primary/10 border-accent-primary text-accent-primary font-medium'
                : 'bg-bg-elevated border-border-subtle text-text-secondary'
            }`}
          >
            {filterOption.label}
          </button>
        ))}

        <div className="text-xs text-text-muted ml-auto">
          {filtered.length} of {allCompanies.length} companies
        </div>
      </div>

      {/* Table */}
      <div className="w-full flex flex-col h-full bg-bg-surface rounded-card border border-border-subtle overflow-hidden">
        <div className="overflow-auto flex-grow">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Company</TableHead>
                <TableHead>Markets</TableHead>
                <TableHead>BD Tags</TableHead>
                <TableHead>HubSpot Status</TableHead>
                <TableHead>Deal</TableHead>
                <TableHead>Last Synced</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8 text-text-secondary animate-pulse">
                    Loading companies...
                  </TableCell>
                </TableRow>
              ) : filtered.length > 0 ? (
                filtered.map((company: any) => (
                  <TableRow key={company.id}>
                    <TableCell className="font-medium text-text-primary">
                      {company.company_name}
                    </TableCell>
                    <TableCell className="text-xs text-text-secondary">
                      {company.countries?.join(", ") || "—"}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1 flex-wrap">
                        {company.bd_tags?.slice(0, 2).map((tag: string) => (
                          <Badge key={tag} variant="default" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${
                          company.hubspot_company_id ? 'bg-green-500' : 'bg-gray-400'
                        }`} />
                        <span className={`text-sm ${
                          company.hubspot_company_id ? 'text-green-600' : 'text-gray-600'
                        }`}>
                          {company.hubspot_company_id ? 'Synced' : 'Not synced'}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {company.hubspot_deal_id ? (
                        <div className="flex items-center gap-1">
                          <Zap className="h-3 w-3 text-accent-primary" />
                          <span className="text-xs text-accent-primary">Active</span>
                        </div>
                      ) : (
                        <span className="text-xs text-text-muted">—</span>
                      )}
                    </TableCell>
                    <TableCell className="text-xs text-text-secondary">
                      {company.hubspot_synced_at ? relativeTime(company.hubspot_synced_at) : "—"}
                    </TableCell>
                    <TableCell>
                      {company.hubspot_company_id ? (
                        <a
                          href={`https://app.hubspot.com/contacts/${company.hubspot_company_id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-text-secondary hover:text-accent-primary flex items-center gap-1 transition-colors"
                        >
                          View in HubSpot
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      ) : (
                        <span className="text-xs text-text-muted">—</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8 text-text-secondary">
                    No companies match the current filters
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  );
}

function HubSpotHistoryTab() {
  const [history, setHistory] = useState<SyncHistoryEntry[]>(getSyncHistory());

  const handleRefresh = () => {
    setHistory(getSyncHistory());
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div className="text-xs text-text-muted italic">
          History is stored for this browser session only. It resets on page refresh.
        </div>
        <Button onClick={handleRefresh} variant="outline" size="sm">
          <RefreshCw className="h-3 w-3 mr-2" />
          Refresh
        </Button>
      </div>

      {history.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <CircleDot className="h-8 w-8 text-text-muted mb-4" />
            <h3 className="text-lg font-medium text-text-primary mb-2">No sync history yet</h3>
            <p className="text-sm text-text-muted text-center">
              Sync history appears here after your first sync runs.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {history.map((entry) => (
            <Card key={entry.id} className="bg-bg-surface border border-border-subtle rounded-xl">
              <CardContent className="p-4">
                <div className="flex justify-between items-center mb-3">
                  <div className="flex items-center gap-2">
                    {entry.status === 'completed' ? (
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                    ) : (
                      <AlertTriangle className="h-4 w-4 text-red-400" />
                    )}
                    <span className="text-sm font-medium text-text-primary">
                      {relativeTime(entry.triggered_at)}
                    </span>
                    <span className="text-xs text-text-muted">
                      {new Date(entry.triggered_at).toLocaleString()}
                    </span>
                  </div>
                  <div className="text-xs text-text-muted bg-bg-elevated px-2 py-0.5 rounded border border-border-subtle">
                    {entry.duration_seconds}s
                  </div>
                </div>

                {entry.status === 'completed' && (
                  <div className="flex gap-6 flex-wrap text-xs">
                    <div className="flex items-center gap-1.5">
                      <span className="font-medium text-text-primary">{entry.companies_synced}</span>
                      <span className="text-text-secondary">companies</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="font-medium text-text-primary">{entry.notes_created}</span>
                      <span className="text-text-secondary">notes</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="font-medium text-text-primary">{entry.deals_created}</span>
                      <span className="text-text-secondary">deals</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="font-medium text-text-primary">{entry.contacts_synced}</span>
                      <span className="text-text-secondary">contacts</span>
                    </div>
                  </div>
                )}

                {entry.status === 'failed' && entry.error && (
                  <div className="mt-2 text-xs text-red-400">
                    {entry.error}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

interface HubSpotSetupTabProps {
  onSetupComplete: () => void;
}

function HubSpotSetupTab({ onSetupComplete }: HubSpotSetupTabProps) {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [setupDone, setSetupDone] = useState(false);

  const { mutate: saveApiKeyMutation, isPending: saveApiKeyPending, error: saveApiKeyError } = useMutation({
    mutationFn: (apiKey: string) => saveHubSpotAPIKey(apiKey),
    onSuccess: () => {
      setStep(2);
    },
  });

  const { mutate: setupMutation, isPending: setupPending, error: setupError } = useMutation({
    mutationFn: setupHubSpotProperties,
    onSuccess: () => setSetupDone(true),
  });

  const { mutate: testMutation, data: testResult, isPending: testPending } = useMutation({
    mutationFn: () => triggerHubSpotSync(1),
  });

  const handleSaveApiKey = () => {
    if (apiKeyInput.trim()) {
      saveApiKeyMutation(apiKeyInput);
    }
  };

  const handleTestSync = () => {
    testMutation();
  };

  return (
    <div className="max-w-lg mx-auto space-y-6">
      {/* Step Indicator */}
      <div className="flex items-center gap-2 mb-8">
        {[1, 2, 3].map((stepNum) => (
          <div key={stepNum} className="flex items-center">
            <div className={`h-8 w-8 rounded-full flex items-center justify-center text-sm font-medium ${
              step > stepNum ? 'bg-green-500 text-white' :
              step === stepNum ? 'bg-accent-primary text-white' :
              'bg-bg-elevated text-text-muted border border-border-subtle'
            }`}>
              {step > stepNum ? '✓' : stepNum}
            </div>
            <span className="text-xs text-text-secondary mt-6 ml-1">
              {stepNum === 1 ? 'Connect' : stepNum === 2 ? 'Configure' : 'Test'}
            </span>
            {stepNum < 3 && (
              <div className="flex-1 h-px bg-border-subtle ml-2" />
            )}
          </div>
        ))}
      </div>

      {/* Step 1: Connect */}
      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-text-primary">Add your HubSpot API key</CardTitle>
            <p className="text-sm text-text-secondary">
              Create a Private App in HubSpot and paste the token below. Required scopes:
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              {[
                'crm.objects.companies.read',
                'crm.objects.companies.write',
                'crm.objects.contacts.read',
                'crm.objects.contacts.write',
                'crm.objects.deals.read',
                'crm.objects.deals.write',
              ].map((scope) => (
                <div key={scope} className="bg-bg-elevated border border-border-subtle rounded px-2 py-0.5 text-xs font-mono text-text-secondary">
                  {scope}
                </div>
              ))}
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-text-primary">Private App Token</label>
              <input
                type="password"
                placeholder="pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                value={apiKeyInput}
                onChange={(e) => setApiKeyInput(e.target.value)}
                className="w-full border border-border-default rounded-md bg-bg-base text-text-primary px-3 py-2 text-sm"
              />
              <p className="text-xs text-text-muted">
                Your token is securely saved to the database. No server restart required.
              </p>
            </div>

            {saveApiKeyError && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-xs text-red-400">
                Failed to save API key. Please try again.
              </div>
            )}

            <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3 text-xs text-green-500">
              ✓ Once saved, your token is immediately available to JobIntel.
            </div>

            <div className="flex justify-end">
              <Button
                onClick={handleSaveApiKey}
                disabled={!apiKeyInput.trim() || saveApiKeyPending}
              >
                {saveApiKeyPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                {saveApiKeyPending ? 'Saving...' : 'Save & Configure →'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Configure */}
      {step === 2 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-text-primary">Create HubSpot custom properties</CardTitle>
            <p className="text-sm text-text-secondary">
              JobIntel needs 4 custom properties on your HubSpot Company object to store hiring signals.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              {[
                { name: 'jobintel_id', type: 'string' },
                { name: 'hiring_velocity_score', type: 'number' },
                { name: 'bd_tags', type: 'string' },
                { name: 'total_postings_7d', type: 'number' },
              ].map((prop) => (
                <div key={prop.name} className="flex justify-between items-center p-3 bg-bg-elevated rounded-lg border border-border-subtle">
                  <code className="font-mono text-sm text-text-primary">{prop.name}</code>
                  <span className="text-xs text-text-secondary">{prop.type}</span>
                </div>
              ))}
            </div>

            <div className="flex justify-between">
              <Button variant="outline" onClick={() => setStep(1)}>
                ← Back
              </Button>
              <Button
                onClick={() => setupMutation()}
                disabled={setupPending || setupDone}
              >
                {setupPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                {setupDone && <CheckCircle2 className="h-4 w-4 mr-2" />}
                {setupPending ? 'Creating...' : setupDone ? 'Properties Created ✓' : 'Create Properties'}
              </Button>
            </div>

            {setupDone && (
              <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3 text-xs text-green-500">
                ✓ All 4 custom properties created successfully. You can now proceed to test the connection.
                <Button onClick={() => setStep(3)} className="mt-2">
                  Next: Test →
                </Button>
              </div>
            )}

            {setupError && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-xs text-red-400">
                Failed to create properties. Check that your HUBSPOT_API_KEY is correct and the server is running.
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Step 3: Test */}
      {step === 3 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-text-primary">Test your connection</CardTitle>
            <p className="text-sm text-text-secondary">
              Run a test sync to confirm everything is working correctly.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              onClick={handleTestSync}
              disabled={testPending}
              className="w-full"
            >
              {testPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {!testPending && <Zap className="h-4 w-4 mr-2" />}
              Run Test Sync (last 1 hour)
            </Button>

            {testResult && (
              <div className={`rounded-lg p-4 ${
                testResult.status === 'completed'
                  ? 'bg-green-500/10 border border-green-500/20'
                  : 'bg-red-500/10 border border-red-500/20'
              }`}>
                {testResult.status === 'completed' ? (
                  <>
                    <div className="flex items-center gap-2 text-sm font-medium text-green-500 mb-2">
                      <CheckCircle2 className="h-5 w-5" />
                      Connection successful!
                    </div>
                    <p className="text-xs text-text-secondary mb-3">
                      {(testResult as any).summary?.companies_synced || 0} companies synced to HubSpot
                    </p>
                    <Button onClick={onSetupComplete}>
                      Go to Overview →
                    </Button>
                  </>
                ) : (
                  <>
                    <div className="flex items-center gap-2 text-sm font-medium text-red-400 mb-2">
                      <AlertTriangle className="h-5 w-5" />
                      Connection failed
                    </div>
                    {(testResult as any).summary?.error && (
                      <p className="text-xs text-red-400">
                        {(testResult as any).summary.error}
                      </p>
                    )}
                  </>
                )}
              </div>
            )}

            <div className="pt-4 border-t border-border-subtle">
              <h4 className="text-sm font-medium text-text-primary mb-3">Need help?</h4>
              <div className="space-y-2">
                {[
                  "Make sure HUBSPOT_API_KEY is set in your backend .env file",
                  "Ensure your Private App has all required CRM scopes enabled",
                  "Run POST /api/v1/hubspot/setup from Swagger if properties are missing",
                ].map((help) => (
                  <div key={help} className="flex items-start gap-2 text-xs text-text-secondary">
                    <ArrowRight className="h-3 w-3 text-accent-primary mt-0.5 flex-shrink-0" />
                    {help}
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-start">
              <Button variant="outline" onClick={() => setStep(2)}>
                ← Back to Configure
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}