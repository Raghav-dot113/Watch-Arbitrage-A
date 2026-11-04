"use client";

import React from "react";
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import { PageHeader } from "../../../../components/shell/PageHeader";
import { PageContainer } from "../../../../components/ui/PageContainer";
import { EmptyState } from "../../../../components/ui/EmptyState";
import { ErrorState } from "../../../../components/ui/ErrorState";
import { LoadingState } from "../../../../components/ui/LoadingState";
import {
  useOrganizationSettings,
  useUpdateOrganizationSettings,
  useSubscription,
  useCreateCheckoutSession,
  useCreatePortalSession,
  useIntegrationStatus,
  useLinkTelegram,
  useUnlinkTelegram,
  useRegisterPushDevice,
  useUnregisterPushDevice,
  type FeeDefaults,
  type OrganizationSettingsResponse,
  type OrganizationSettingsPatchRequest,
  type SubscriptionResponse,
  type IntegrationStatusResponse,
} from "../../../../lib/hooks/useSettings";
import { formatDate } from "../../../../lib/formatters";

const FEE_FIELDS: Array<{ key: keyof FeeDefaults; label: string }> = [
  { key: "buyer_fee", label: "Buyer fee" },
  { key: "tax_and_duty", label: "Tax & duty" },
  { key: "inbound_shipping", label: "Inbound shipping" },
  { key: "authentication_cost", label: "Authentication cost" },
  { key: "service_reserve", label: "Service reserve" },
  { key: "financing_cost", label: "Financing cost" },
  { key: "acquisition_risk_reserve", label: "Acquisition risk reserve" },
  { key: "selling_fee", label: "Selling fee" },
  { key: "outbound_shipping", label: "Outbound shipping" },
  { key: "resale_payment_cost", label: "Resale payment cost" },
  { key: "exit_risk_reserve", label: "Exit risk reserve" },
];

export default function SettingsPage() {
  const [tab, setTab] = React.useState("organization");

  const { data: settings, isLoading: settingsLoading } = useOrganizationSettings();
  const updateSettings = useUpdateOrganizationSettings();
  const [settingsDialogOpen, setSettingsDialogOpen] = React.useState(false);
  const [settingsForm, setSettingsForm] = React.useState<{
    currency: string;
    timezone: string;
    fees: Record<string, string>;
  }>({ currency: "", timezone: "", fees: {} });

  const { data: subscription } = useSubscription();
  const createCheckout = useCreateCheckoutSession();
  const createPortal = useCreatePortalSession();
  const [planId, setPlanId] = React.useState("");
  const [checkoutUrl, setCheckoutUrl] = React.useState<string | null>(null);

  const { data: integrations } = useIntegrationStatus();
  const linkTelegram = useLinkTelegram();
  const unlinkTelegram = useUnlinkTelegram();
  const registerPush = useRegisterPushDevice();
  const unregisterPush = useUnregisterPushDevice();
  const [telegramDialogOpen, setTelegramDialogOpen] = React.useState(false);
  const [pushPlatform, setPushPlatform] = React.useState<"ios" | "android">("ios");
  const [pushToken, setPushToken] = React.useState("");

  const orgSettings: OrganizationSettingsResponse | undefined = settings;
  const subscriptionData: SubscriptionResponse | undefined = subscription;
  const integrationStatus: IntegrationStatusResponse | undefined = integrations;

  const handleSettingsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (updateSettings.isPending) return;
    const defaultFees: FeeDefaults = {} as FeeDefaults;
    for (const field of FEE_FIELDS) {
      defaultFees[field.key as keyof FeeDefaults] = settingsForm.fees[field.key as keyof FeeDefaults] || null;
    }
    await updateSettings.mutateAsync({
      currency: settingsForm.currency || undefined,
      timezone: settingsForm.timezone || undefined,
      default_fees: defaultFees,
    });
    setSettingsDialogOpen(false);
  };

  const handleCheckout = async () => {
    if (createCheckout.isPending) return;
    const result = await createCheckout.mutateAsync({ plan_id: planId });
    setCheckoutUrl(result.url);
    window.open(result.url, "_blank");
  };

  const handlePortal = async () => {
    if (createPortal.isPending) return;
    const result = await createPortal.mutateAsync();
    setCheckoutUrl(result.url);
    window.open(result.url, "_blank");
  };

  const handleLinkTelegram = async () => {
    if (linkTelegram.isPending) return;
    const result = await linkTelegram.mutateAsync();
    setTelegramDialogOpen(true);
  };

  const handleUnlinkTelegram = async () => {
    if (unlinkTelegram.isPending) return;
    await unlinkTelegram.mutateAsync();
  };

  const handleRegisterPush = async () => {
    if (registerPush.isPending) return;
    await registerPush.mutateAsync({
      platform: pushPlatform,
      device_token: pushToken,
    });
    setPushPlatform("ios");
    setPushToken("");
  };

  const handleUnregisterPush = async (deviceId: string) => {
    if (unregisterPush.isPending) return;
    await unregisterPush.mutateAsync(deviceId);
  };

  if (settingsLoading) {
    return (
      <PageContainer>
        <LoadingState label="Loading settings" fullPage />
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <PageHeader
        title="Settings"
        description="Manage organization, billing, and integrations."
      />
      <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
        <Tabs
          value={tab}
          onChange={(_, newValue) => setTab(newValue as string)}
          sx={{ minWidth: 300 }}
        >
          <Tab label="Organization" value="organization" />
          <Tab label="Billing" value="billing" />
          <Tab label="Integrations" value="integrations" />
        </Tabs>

        {tab === "organization" && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
              Organization Settings
            </Typography>
            <Box
              sx={{
                p: 2,
                bgcolor: "background.paper",
                border: `1px solid`,
                borderColor: "divider",
                borderRadius: "md",
              }}
            >
              {orgSettings ? (
                <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                    Currency
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {orgSettings.currency}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                    Timezone
                  </Typography>
                  <Typography variant="body2">{orgSettings.timezone}</Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                    Default Fees
                  </Typography>
                  <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
                    {FEE_FIELDS.map((field) => {
                      const value = orgSettings.default_fees[field.key as keyof FeeDefaults];
                      return (
                        <Chip
                          key={field.key as string}
                          label={`${field.label}: ${value ?? "—"}`}
                          size="small"
                          variant="outlined"
                        />
                      );
                    })}
                  </Box>
                </Box>
              ) : (
                <EmptyState title="No organization settings" />
              )}
            </Box>
            <Button
              variant="outlined"
              onClick={() => {
                setSettingsForm({
                  currency: orgSettings?.currency ?? "",
                  timezone: orgSettings?.timezone ?? "",
                  fees: {},
                });
                setSettingsDialogOpen(true);
              }}
            >
              Edit Organization Settings
            </Button>
          </Box>
        )}

        {tab === "billing" && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
              Billing & Subscription
            </Typography>
            <Box
              sx={{
                p: 2,
                bgcolor: "background.paper",
                border: `1px solid`,
                borderColor: "divider",
                borderRadius: "md",
              }}
            >
              {subscriptionData ? (
                <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                    Plan
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {subscriptionData.plan_id ?? "None"}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                    Status
                  </Typography>
                  <Chip
                    label={subscriptionData.status}
                    size="small"
                    variant="outlined"
                    color={
                      subscriptionData.status === "active"
                        ? "success"
                        : "default"
                    }
                  />
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                    Current Period
                  </Typography>
                  <Typography variant="body2">
                    {formatDate(subscriptionData.current_period_start ?? "")} —{" "}
                    {formatDate(subscriptionData.current_period_end ?? "")}
                  </Typography>
                  {subscriptionData.trial_end && (
                    <Box>
                      <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                        Trial Ends
                      </Typography>
                      <Typography variant="body2">
                        {formatDate(subscriptionData.trial_end)}
                      </Typography>
                    </Box>
                  )}
                </Box>
              ) : (
                <EmptyState title="No active subscription" />
              )}
            </Box>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                Checkout
              </Typography>
              <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                <TextField
                  required
                  label="Plan ID"
                  value={planId}
                  onChange={(e) => setPlanId(e.target.value)}
                  helperText="Stripe plan ID to subscribe to"
                />
                <Box sx={{ display: "flex", gap: 1 }}>
                  <Button
                    variant="contained"
                    onClick={handleCheckout}
                    disabled={createCheckout.isPending}
                  >
                    Start Checkout
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={handlePortal}
                    disabled={createPortal.isPending}
                  >
                    Customer Portal
                  </Button>
                </Box>
              </Box>
            </Box>
          </Box>
        )}

        {tab === "integrations" && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
              Integrations
            </Typography>
            <Box
              sx={{
                p: 2,
                bgcolor: "background.paper",
                border: `1px solid`,
                borderColor: "divider",
                borderRadius: "md",
              }}
            >
              {integrationStatus ? (
                <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                    Telegram
                  </Typography>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <Chip
                      label={integrationStatus.telegram_status}
                      size="small"
                      variant="outlined"
                      color={
                        integrationStatus.telegram_status === "connected"
                          ? "success"
                          : integrationStatus.telegram_status === "pending"
                            ? "warning"
                            : "default"
                      }
                    />
                    {integrationStatus.telegram_status === "connected" && (
                      <Button
                        size="small"
                        variant="outlined"
                        color="error"
                        onClick={handleUnlinkTelegram}
                        disabled={unlinkTelegram.isPending}
                      >
                        Unlink
                      </Button>
                    )}
                    {integrationStatus.telegram_status !== "connected" && (
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={handleLinkTelegram}
                        disabled={linkTelegram.isPending}
                      >
                        Link
                      </Button>
                    )}
                  </Box>
                  {integrationStatus.telegram_link_expires_at && (
                    <Typography variant="caption" color="text.secondary">
                      Link expires {formatDate(integrationStatus.telegram_link_expires_at)}
                    </Typography>
                  )}
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, mb: 0.5 }}>
                    Push Devices
                  </Typography>
                  {integrationStatus.push_devices.length === 0 ? (
                    <Typography variant="caption" color="text.disabled">
                      No push devices registered.
                    </Typography>
                  ) : (
                    <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
                      {integrationStatus.push_devices.map((device) => (
                        <Box
                          key={device.id}
                          sx={{
                            display: "flex",
                            alignItems: "center",
                            gap: 1,
                            p: 1,
                            bgcolor: "action.hover",
                            borderRadius: "md",
                          }}
                        >
                          <Typography variant="caption" sx={{ flex: 1 }}>
                            {device.platform}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {formatDate(device.created_at)}
                          </Typography>
                          <Button
                            size="small"
                            variant="text"
                            onClick={() => handleUnregisterPush(device.id)}
                            disabled={unregisterPush.isPending}
                          >
                            Remove
                          </Button>
                        </Box>
                      ))}
                    </Box>
                  )}
                </Box>
              ) : (
                <EmptyState title="No integration status" />
              )}
            </Box>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                Register Push Device
              </Typography>
              <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                <TextField
                  select
                  label="Platform"
                  value={pushPlatform}
                  onChange={(e) => setPushPlatform(e.target.value as "ios" | "android")}
                >
                  <MenuItem value="ios">iOS</MenuItem>
                  <MenuItem value="android">Android</MenuItem>
                </TextField>
                <TextField
                  required
                  label="Device Token"
                  value={pushToken}
                  onChange={(e) => setPushToken(e.target.value)}
                  helperText="Push device token from your mobile app"
                />
                <Button
                  variant="contained"
                  onClick={handleRegisterPush}
                  disabled={registerPush.isPending}
                >
                  Register
                </Button>
              </Box>
            </Box>
          </Box>
        )}
      </Box>

      <Dialog
        open={settingsDialogOpen}
        onClose={() => setSettingsDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ fontWeight: 600 }}>Edit Organization Settings</DialogTitle>
        <DialogContent sx={{ py: 2 }}>
          <form onSubmit={handleSettingsSubmit}>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
              <TextField
                required
                label="Currency"
                value={settingsForm.currency}
                onChange={(e) => setSettingsForm({ ...settingsForm, currency: e.target.value })}
                helperText="ISO currency code (e.g. USD)"
              />
              <TextField
                required
                label="Timezone"
                value={settingsForm.timezone}
                onChange={(e) => setSettingsForm({ ...settingsForm, timezone: e.target.value })}
                helperText="IANA timezone (e.g. America/New_York)"
              />
              <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                  Default Fees
                </Typography>
                {FEE_FIELDS.map((field) => {
                  const feeKey = field.key as keyof FeeDefaults;
                  return (
                    <TextField
                      key={field.key as string}
                      label={field.label}
                      type="text"
                      inputMode="decimal"
                      value={settingsForm.fees[feeKey] ?? ""}
                      onChange={(e) =>
                        setSettingsForm({
                          ...settingsForm,
                          fees: { ...settingsForm.fees, [feeKey]: e.target.value },
                        })
                      }
                      helperText="Decimal string (e.g. 10.00)"
                    />
                  );
                })}
              </Box>
              <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 1, mt: 1 }}>
                <Button type="button" onClick={() => setSettingsDialogOpen(false)}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={updateSettings.isPending}
                >
                  Save
                </Button>
              </Box>
            </Box>
          </form>
        </DialogContent>
      </Dialog>

      {checkoutUrl && (
        <Dialog
          open={!!checkoutUrl}
          onClose={() => setCheckoutUrl(null)}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle sx={{ fontWeight: 600 }}>Checkout</DialogTitle>
          <DialogContent sx={{ py: 2 }}>
            <Typography variant="body2">
              Redirecting to Stripe Checkout...
            </Typography>
          </DialogContent>
        </Dialog>
      )}

      <Dialog
        open={telegramDialogOpen}
        onClose={() => setTelegramDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ fontWeight: 600 }}>Link Telegram</DialogTitle>
        <DialogContent sx={{ py: 2 }}>
          <Typography variant="body2">
            Click the link below to connect your Telegram account.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 2, pb: 2 }}>
          <Button onClick={() => setTelegramDialogOpen(false)}>Done</Button>
        </DialogActions>
      </Dialog>
    </PageContainer>
  );
}
