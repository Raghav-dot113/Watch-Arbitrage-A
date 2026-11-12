import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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
  isLoading: boolean;
  isError: boolean;
  error: unknown;
  refetch: () => void;
}

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
          url: "https://retailer.example.test/used",
          domain: "retailer.example.test",
          price: { amount: "1000", currency: "USD" },
          availability: "InStock",
          condition: "used",
          max_commission_rate: null,
        },
      ],
      structured_attributes: {},
    },
  ],
  next_page_token: null,
  fetched_at: "2026-11-12T00:00:00Z",
  filtered_out_count: 12,
  provider_pages_fetched: 1,
};

const idleResult: SearchQueryResult = {
  data: undefined,
  isLoading: false,
  isError: false,
  error: null,
  refetch,
};

let queryResult: SearchQueryResult = idleResult;

function configureQueryResult(result: SearchQueryResult = idleResult): void {
  queryResult = result;
  mockUseChannel3Search.mockImplementation(
    (params: Channel3SearchRequest | null) => (params ? queryResult : idleResult),
  );
}

beforeEach(() => {
  refetch.mockReset();
  mockUseChannel3Search.mockReset();
  configureQueryResult();
});

describe("SearchPage", () => {
  it("defaults to pre-owned and sends the selected filters", async () => {
    const user = userEvent.setup();
    render(<SearchPage />);

    expect(screen.getByRole("button", { name: "Pre-owned" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    const queryInput = screen.getByPlaceholderText(/Search watches/);
    await user.type(queryInput, "Rolex");
    await user.click(screen.getByRole("button", { name: "Search" }));

    expect(mockUseChannel3Search).toHaveBeenLastCalledWith({
      query: "Rolex",
      limit: 20,
      condition: "used",
      in_stock_only: false,
    });

    await user.click(screen.getByRole("button", { name: "New" }));
    await user.click(screen.getByRole("checkbox", { name: "In stock only" }));
    await user.click(screen.getByRole("button", { name: "Search" }));

    expect(mockUseChannel3Search).toHaveBeenLastCalledWith({
      query: "Rolex",
      limit: 20,
      condition: "new",
      in_stock_only: true,
    });

    await user.click(screen.getByRole("button", { name: "All" }));
    await user.click(screen.getByRole("button", { name: "Search" }));

    expect(mockUseChannel3Search).toHaveBeenLastCalledWith({
      query: "Rolex",
      limit: 20,
      condition: "all",
      in_stock_only: true,
    });
  });

  it("renders product and offer condition chips with hidden-offer count", async () => {
    const user = userEvent.setup();
    configureQueryResult({ ...idleResult, data: response });
    render(<SearchPage />);

    await user.type(
      screen.getByPlaceholderText(/Search watches/),
      "Rolex{enter}",
    );

    expect(await screen.findAllByText("Rolex Submariner")).toHaveLength(2);
    expect(
      screen.getByLabelText("Product condition: Pre-owned"),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Pre-owned offer condition"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("12 offers hidden by the active filters."),
    ).toBeInTheDocument();
  });

  it("mentions the active condition in the empty state", async () => {
    const user = userEvent.setup();
    configureQueryResult({ ...idleResult, data: { ...response, products: [] } });
    render(<SearchPage />);

    await user.click(screen.getByRole("button", { name: "New" }));
    await user.type(
      screen.getByPlaceholderText(/Search watches/),
      "Rolex{enter}",
    );

    expect(
      await screen.findByText(/No new results for "Rolex"/),
    ).toBeInTheDocument();
  });
});
