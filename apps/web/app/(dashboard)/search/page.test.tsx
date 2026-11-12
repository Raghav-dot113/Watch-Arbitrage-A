import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpError } from "@chronoarb/api-client";
import type {
  Channel3SearchRequest,
  Channel3SearchResponse,
} from "../../../lib/api/types";
import SearchPage from "./page";

const { mockUseChannel3Search } = vi.hoisted(() => ({
  mockUseChannel3Search: vi.fn(),
}));

vi.mock("../../../lib/hooks", () => ({
  useChannel3Search: mockUseChannel3Search,
}));

const refetch = vi.fn();
interface SearchQueryResult {
  data: Channel3SearchResponse | undefined;
  isFetching: boolean;
  isError: boolean;
  error: unknown;
  refetch: () => void;
}

const idleResult: SearchQueryResult = {
  data: undefined,
  isFetching: false,
  isError: false,
  error: null,
  refetch,
};

const response: Channel3SearchResponse = {
  products: [
    {
      id: "watch-1",
      title: "Rolex Submariner",
      description: null,
      brands: [{ id: "rolex", name: "Rolex" }],
      images: [],
      category: null,
      materials: null,
      key_features: null,
      offers: [
        {
          url: "https://retailer.example.test/out-of-stock",
          domain: "retailer.example.test",
          price: { amount: "900", currency: "USD" },
          availability: "OutOfStock",
          condition: "new",
          max_commission_rate: null,
        },
        {
          url: "https://retailer.example.test/used",
          domain: "retailer.example.test",
          price: { amount: "1000", currency: "USD" },
          availability: "InStock",
          condition: "used",
          max_commission_rate: null,
        },
        {
          url: "https://retailer.example.test/new",
          domain: "retailer.example.test",
          price: { amount: "1200", currency: "USD" },
          availability: "InStock",
          condition: "new",
          max_commission_rate: null,
        },
        {
          url: "https://retailer.example.test/no-price",
          domain: "retailer.example.test",
          price: null,
          availability: "InStock",
          condition: null,
          max_commission_rate: null,
        },
      ],
      structured_attributes: {},
    },
  ],
  next_page_token: null,
  fetched_at: "2026-11-12T00:00:00Z",
};

let queryResult: SearchQueryResult = idleResult;

function configureQueryResult(result: SearchQueryResult = idleResult): void {
  queryResult = result;
  mockUseChannel3Search.mockImplementation(
    (params: Channel3SearchRequest | null) => (params ? queryResult : idleResult),
  );
}

function createHttpError(status: number, code: string, message: string): HttpError {
  return new HttpError(status, {
    code,
    message,
    field_errors: null,
    trace_id: "trc_search_test",
    retryable: false,
  });
}

beforeEach(() => {
  refetch.mockReset();
  mockUseChannel3Search.mockReset();
  configureQueryResult();
});

describe("SearchPage", () => {
  it("submits a search when the Search button is clicked", async () => {
    const user = userEvent.setup();
    configureQueryResult({
      ...idleResult,
      data: response,
      isError: false,
      error: null,
    });

    render(<SearchPage />);
    await user.type(screen.getByRole("textbox", { name: "Search watches" }), "Omega");
    await user.click(screen.getByRole("button", { name: "Search" }));

    expect(await screen.findByText("Rolex Submariner")).toBeInTheDocument();
    expect(mockUseChannel3Search).toHaveBeenLastCalledWith({
      query: "Omega",
      limit: 20,
    });
  });

  it("renders provider results, preferring the cheapest in-stock offer", async () => {
    const user = userEvent.setup();
    configureQueryResult({
      ...idleResult,
      data: response,
      isError: false,
      error: null,
    });

    render(<SearchPage />);
    const searchInput = screen.getByRole("textbox", { name: "Search watches" });
    await user.type(searchInput, "Rolex Submariner{enter}");

    expect(await screen.findByText("Rolex Submariner")).toBeInTheDocument();
    expect(screen.getByText("$1,000.00")).toBeInTheDocument();
    expect(screen.getByText("used")).toBeInTheDocument();
    const watchButton = screen.getByRole("button", { name: "Watch" });
    expect(watchButton).toBeDisabled();
    await user.hover(watchButton.parentElement!);
    expect(await screen.findByRole("tooltip")).toHaveTextContent("Coming soon");
  });

  it("shows an empty state when the provider returns no products", async () => {
    const user = userEvent.setup();
    configureQueryResult({
      ...idleResult,
      data: { ...response, products: [] },
      isError: false,
      error: null,
    });

    render(<SearchPage />);
    await user.type(
      screen.getByRole("textbox", { name: "Search watches" }),
      "Rolex{enter}",
    );

    expect(await screen.findByText("No watches found")).toBeInTheDocument();
  });

  it("keeps the form visible and shows the not-configured API error", async () => {
    const user = userEvent.setup();
    configureQueryResult({
      ...idleResult,
      isError: true,
      error: createHttpError(
        503,
        "not_configured",
        "Search provider is not configured.",
      ),
    });

    render(<SearchPage />);
    const searchInput = screen.getByRole("textbox", { name: "Search watches" });
    await user.type(searchInput, "Rolex{enter}");

    expect(screen.getByRole("textbox", { name: "Search watches" })).toBeInTheDocument();
    expect(
      await screen.findByText("Search provider is not configured. (not_configured)"),
    ).toBeInTheDocument();
  });

  it("shows the credits error returned by the API", async () => {
    const user = userEvent.setup();
    configureQueryResult({
      ...idleResult,
      isError: true,
      error: createHttpError(
        503,
        "credits_exhausted",
        "Search credits are exhausted. Contact your administrator.",
      ),
    });

    render(<SearchPage />);
    await user.type(
      screen.getByRole("textbox", { name: "Search watches" }),
      "Rolex{enter}",
    );

    expect(
      await screen.findByText(
        "Search credits are exhausted. Contact your administrator. (credits_exhausted)",
      ),
    ).toBeInTheDocument();
  });

  it("retries the same search when the form is submitted after an error", async () => {
    const user = userEvent.setup();
    configureQueryResult({
      ...idleResult,
      isError: true,
      error: createHttpError(503, "not_configured", "Search provider is not configured."),
    });

    const { rerender } = render(<SearchPage />);
    const searchInput = screen.getByRole("textbox", { name: "Search watches" });
    await user.type(searchInput, "Rolex{enter}");
    expect(await screen.findByText(/not_configured/)).toBeInTheDocument();

    queryResult = { ...idleResult, data: response, isError: false, error: null };
    await user.click(screen.getByRole("button", { name: "Search" }));
    expect(refetch).toHaveBeenCalledOnce();
    rerender(<SearchPage />);

    expect(await screen.findByText("Rolex Submariner")).toBeInTheDocument();
  });

  it.each([
    ["99", 50],
    ["0", 1],
  ])("clamps limit %s to %i when submitting", (inputValue, expectedLimit) => {
    const observedRequests: Channel3SearchRequest[] = [];
    mockUseChannel3Search.mockImplementation(
      (params: Channel3SearchRequest | null) => {
        if (params) observedRequests.push(params);
        return params ? queryResult : idleResult;
      },
    );

    render(<SearchPage />);
    const limitInput = screen.getByRole("spinbutton", { name: "Results limit" });
    expect(limitInput).toHaveAttribute("min", "1");
    expect(limitInput).toHaveAttribute("max", "50");
    fireEvent.change(limitInput, { target: { value: inputValue } });
    fireEvent.change(screen.getByRole("textbox", { name: "Search watches" }), {
      target: { value: "Rolex" },
    });
    const form = screen.getByRole("textbox", { name: "Search watches" }).closest("form");
    expect(form).not.toBeNull();
    fireEvent.submit(form!);

    expect(observedRequests.at(-1)?.limit).toBe(expectedLimit);
  });

  it("shows the minimum query requirement and clears the form", async () => {
    const user = userEvent.setup();
    render(<SearchPage />);
    const searchInput = screen.getByRole("textbox", { name: "Search watches" });

    await user.type(searchInput, "R{enter}");
    expect(
      screen.getByText("Enter at least 2 characters."),
    ).toBeInTheDocument();
    expect(mockUseChannel3Search).toHaveBeenCalledWith(null);

    await user.click(screen.getByRole("button", { name: "Clear" }));
    expect(searchInput).toHaveValue("");
    expect(screen.getByRole("spinbutton", { name: "Results limit" })).toHaveValue(20);
  });
});
