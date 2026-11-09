import { useQuery } from "@tanstack/react-query";
import {
  listActivity,
  listTradeOutcomes,
  type ActivityItem,
  type TradeOutcome,
} from "../api";

export function useActivity() {
  return useQuery({
    queryKey: ["activity"],
    queryFn: async () => {
      return listActivity();
    },
  });
}

export function useTradeOutcomes() {
  return useQuery({
    queryKey: ["tradeOutcomes"],
    queryFn: async () => {
      return listTradeOutcomes();
    },
  });
}

export type { ActivityItem, TradeOutcome };
