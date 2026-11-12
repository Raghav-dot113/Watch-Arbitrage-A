"use client";

import dynamic from "next/dynamic";
import type { ComponentType } from "react";
import { LoadingState } from "../ui/LoadingState";
import type { ChronoArbGridProps } from "./ChronoArbGridImpl";

// Bryntum touches browser globals (matchMedia) at module evaluation time. Load it
// only in the browser so Next.js can prerender the dashboard pages.
const LazyGrid = dynamic(
  () => import("./ChronoArbGridImpl").then((module) => module.ChronoArbGrid),
  {
    ssr: false,
    loading: () => <LoadingState label="Loading data grid" />,
  },
) as ComponentType<ChronoArbGridProps<{ id: string }>>;

export type {
  ChronoArbGridAction,
  ChronoArbGridColumn,
  ChronoArbGridProps,
} from "./ChronoArbGridImpl";

export function ChronoArbGrid<Row extends { id: string }>(
  props: ChronoArbGridProps<Row>,
) {
  return <LazyGrid {...(props as unknown as ChronoArbGridProps<{ id: string }>)} />;
}
