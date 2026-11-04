export function formatCurrency(
  value: string | number | null | undefined,
  currency: string = "USD"
): string {
  if (value === null || value === undefined) return "—";
  const num = typeof value === "string" ? Number(value) : value;
  if (Number.isNaN(num)) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
}

export function formatMoney(money: Money | null): string {
  if (!money) return "—";
  return formatCurrency(money.value, money.currency);
}

export interface Money {
  value: string;
  currency: string;
}

export function formatPercent(
  value: string | number | null | undefined,
  decimals: number = 2
): string {
  if (value === null || value === undefined) return "—";
  const num = typeof value === "string" ? Number(value) : value;
  if (Number.isNaN(num)) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num / 100);
}
