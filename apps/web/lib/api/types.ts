export type OpportunityState =
  | "published"
  | "dismissed"
  | "contacted"
  | "purchased"
  | "expired";

export interface Money {
  value: string;
  currency: string;
}

export interface Valuation {
  id: string;
  listing_id: string;
  model_version: string;
  config_version: string;
  cost_assumptions_version: string;
  expected_exit_price: string | null;
  exit_price_currency: string | null;
  all_in_acquisition: string | null;
  expected_net_resale: string | null;
  expected_net_profit: string | null;
  roi: string | null;
  low_estimate: string | null;
  high_estimate: string | null;
  confidence: string | null;
  comparable_count: number | null;
  sample_dispersion: string | null;
  cost_breakdown: Record<string, unknown> | null;
  adjustment_details: Record<string, unknown> | null;
  risk_reserve_details: Record<string, unknown> | null;
  created_at: string;
}

export interface OpportunityListing {
  id: string;
  title: string;
  description: string | null;
  external_url: string | null;
  listing_price: string | null;
  listing_price_currency: string | null;
  normalized_price: string | null;
  normalized_currency: string | null;
  condition: string | null;
  set_status: string | null;
  seller_geography: string | null;
  listed_at: string | null;
  reference_id: string;
  brand_name: string;
  ref_code: string;
  model_name: string | null;
  generation: string | null;
  reference_attributes: Record<string, unknown> | null;
  parsed_attributes: Record<string, unknown> | null;
  source_key: string;
  source_display_name: string;
  match_confidence: string | null;
  match_method: string | null;
  match_features: Record<string, unknown> | null;
  fx_rate: string;
  fx_source: string;
  fx_date: string;
}

export interface Opportunity {
  id: string;
  organization_id: string;
  listing_id: string;
  valuation_id: string;
  material_version: number;
  score: string | null;
  state: OpportunityState;
  positive_factors: Record<string, unknown> | unknown[] | null;
  negative_factors: Record<string, unknown> | unknown[] | null;
  published_at: string | null;
  state_changed_at: string | null;
  created_at: string;
  data_age_seconds: number;
  confidence: string | null;
  valuation_version: string;
  cost_assumptions_version: string;
  my_decision: string | null;
  listing: OpportunityListing;
  valuation: Valuation;
}

export interface OpportunityDetail extends Opportunity {
  observation_at: string;
}

export interface PaginationMeta {
  trace_id: string;
  next_cursor: string | null;
  has_more: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: PaginationMeta;
}

export interface User {
  id: string;
  email: string;
  display_name: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface Membership {
  id: string;
  organization_id: string;
  user_id: string;
  role: string;
  invited_by: string | null;
  created_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  created_at: string;
  updated_at: string | null;
}

export interface OrganizationCreateRequest {
  name: string;
  slug: string;
}

export interface MeResponse {
  user: User;
  memberships: Membership[];
  organizations: Organization[];
}

export interface HealthResponse {
  status: string;
  trace_id: string;
}

export interface ReadyResponse {
  status: string;
  database: string;
  trace_id: string;
}

export interface WatchListEntry {
  id: string;
  watch_list_id: string;
  reference_id: string;
  created_at: string;
}

export interface WatchList {
  id: string;
  organization_id: string;
  name: string;
  created_at: string;
  entries: WatchListEntry[];
}

export interface WatchListCreateRequest {
  name: string;
  reference_ids: string[];
}

export interface WatchListUpdateRequest {
  name: string;
  reference_ids: string[];
}

export type AlertChannel = "in_app" | "push" | "telegram";

export type DeliveryStatus = "pending" | "sent" | "failed" | "suppressed";

export interface AlertRuleFilters {
  reference_ids?: string[] | null;
  min_profit?: string | null;
  max_acquisition?: string | null;
  conditions?: string[] | null;
}

export interface AlertRuleCreateRequest {
  name: string;
  filters: AlertRuleFilters;
  channels: AlertChannel[];
  cooldown_minutes: number;
  is_enabled: boolean;
}

export interface AlertRuleResponse {
  id: string;
  organization_id: string;
  created_by: string;
  name: string;
  filters: AlertRuleFilters;
  channels: AlertChannel[];
  cooldown_minutes: number;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface AlertDeliveryResponse {
  id: string;
  rule_id: string;
  opportunity_id: string;
  material_version: number;
  channel: string;
  delivery_status: DeliveryStatus;
  created_at: string;
}

export interface AlertTestAcceptedResponse {
  event_id: string;
  status: "pending";
}

export type ActivityEventType = "feedback" | "outcome";

export interface ActivityItem {
  id: string;
  event_type: ActivityEventType;
  user_id: string;
  opportunity_id: string | null;
  reference_id: string | null;
  decision: string | null;
  notes: string | null;
  acquisition_price: string | null;
  acquisition_currency: string | null;
  resale_price: string | null;
  resale_currency: string | null;
  actual_profit: string | null;
  days_to_sell: number | null;
  created_at: string;
}

export interface TradeOutcome {
  id: string;
  organization_id: string;
  user_id: string;
  opportunity_id: string | null;
  reference_id: string;
  acquisition_price: string | null;
  acquisition_currency: string | null;
  resale_price: string | null;
  resale_currency: string | null;
  actual_profit: string | null;
  actual_profit_currency: string | null;
  days_to_sell: number | null;
  created_at: string;
}

export interface FeeDefaults {
  buyer_fee: string | null;
  tax_and_duty: string | null;
  inbound_shipping: string | null;
  authentication_cost: string | null;
  service_reserve: string | null;
  financing_cost: string | null;
  acquisition_risk_reserve: string | null;
  selling_fee: string | null;
  outbound_shipping: string | null;
  resale_payment_cost: string | null;
  exit_risk_reserve: string | null;
}

export interface OrganizationSettingsResponse {
  currency: string;
  timezone: string;
  default_fees: FeeDefaults;
}

export interface OrganizationSettingsPatchRequest {
  currency?: string | null;
  timezone?: string | null;
  default_fees?: FeeDefaults | null;
}

export interface SubscriptionResponse {
  id: string | null;
  status: string;
  plan_id: string | null;
  current_period_start: string | null;
  current_period_end: string | null;
  trial_end: string | null;
}

export interface PayPalSubscriptionApprovalResponse {
  subscription_id: string;
  url: string;
}

export interface PayPalCheckoutRequest {
  plan_id: string;
}

export interface IntegrationStatusResponse {
  telegram_status: "disconnected" | "pending" | "connected";
  telegram_link_expires_at: string | null;
  push_devices: PushDeviceResponse[];
}

export interface TelegramLinkResponse {
  link_url: string;
  expires_at: string;
}

export interface PushDeviceResponse {
  id: string;
  platform: "ios" | "android";
  created_at: string;
  updated_at: string;
}

export interface SourceAdmin {
  id: string;
  source_key: string;
  display_name: string;
  adapter_version: string;
  access_mode: string;
  is_enabled: boolean;
  health_status: string;
  last_fetched_at: string | null;
}

export interface SourcePatchRequest {
  is_enabled: boolean;
}

export interface FeatureFlag {
  id: string;
  key: string;
  description: string | null;
  enabled: boolean;
  organization_ids: string[] | null;
  rollout_pct: number;
  expires_at: string | null;
  created_at: string;
}

export interface FeatureFlagPatchRequest {
  enabled?: boolean | null;
  organization_ids?: string[] | null;
  rollout_pct?: number | null;
  expires_at: string | null;
}

export interface AuditEvent {
  id: string;
  organization_id: string | null;
  user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string;
  details: Record<string, unknown> | null;
  trace_id: string | null;
  created_at: string;
}

export interface UnmatchedListing {
  id: string;
  reference_id: string;
  source_key: string;
  title: string | null;
  external_url: string | null;
  match_method: string | null;
  observation_at: string;
}

export interface UnmatchedResolveRequest {
  reference_id: string;
}

export interface DuplicateGroup {
  id: string;
  representative_id: string;
  method: string | null;
  confidence: string | null;
  listing_ids: string[];
  created_at: string;
}

export interface Channel3Price {
  amount: string;
  currency: string;
}

export interface Channel3Brand {
  id: string;
  name: string;
}

export interface Channel3Image {
  url: string;
  cleaned_url: string | null;
  is_main_image: boolean | null;
  shot_type: string | null;
  alt_text: string | null;
}

export interface Channel3Offer {
  url: string;
  domain: string;
  price: Channel3Price;
  availability: string;
  condition: string | null;
  max_commission_rate: string | null;
}

export interface Channel3Product {
  id: string;
  title: string;
  description: string | null;
  brands: Channel3Brand[];
  images: Channel3Image[];
  category: Record<string, unknown> | null;
  materials: string[] | null;
  key_features: string[] | null;
  offers: Channel3Offer[];
  structured_attributes: Record<string, unknown>;
}

export interface Channel3SearchResponse {
  products: Channel3Product[];
  next_page_token: string | null;
  fetched_at: string;
}

export interface Channel3SearchRequest {
  query: string;
  limit: number;
  page_token?: string;
}
