import type { DashboardSnapshot } from "../types";

export const STALE_AFTER_MS = 15 * 60 * 1_000;

interface CalendarDateParts {
  year: number;
  month: number;
  day: number;
}

function calendarParts(now: Date, timeZone: string): CalendarDateParts {
  if (!Number.isFinite(now.getTime())) {
    throw new RangeError("invalid_date");
  }

  const formatter = new Intl.DateTimeFormat("en-US", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  const parts = formatter.formatToParts(now);
  const values = new Map(parts.map((part) => [part.type, part.value]));
  const year = Number(values.get("year"));
  const month = Number(values.get("month"));
  const day = Number(values.get("day"));

  if (
    !Number.isInteger(year) ||
    !Number.isInteger(month) ||
    !Number.isInteger(day) ||
    month < 1 ||
    month > 12 ||
    day < 1 ||
    day > 31
  ) {
    throw new RangeError("invalid_calendar_parts");
  }

  return { year, month, day };
}

function isoDate(year: number, month: number, day: number): string {
  return `${String(year).padStart(4, "0")}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

export function getReportingPeriod(
  now: Date,
  timeZone: string,
): DashboardSnapshot["reportingPeriod"] {
  const parts = calendarParts(now, timeZone);
  return {
    startDate: isoDate(parts.year, parts.month, 1),
    endDate: isoDate(parts.year, parts.month, parts.day),
    timeZone,
  };
}

export function isIsoUtcTimestamp(value: unknown): value is string {
  if (
    typeof value !== "string" ||
    !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(value)
  ) {
    return false;
  }

  const parsed = Date.parse(value);
  return Number.isFinite(parsed) && new Date(parsed).toISOString() === value;
}

export function isMetricStale(updatedAt: string | null, now: Date): boolean {
  if (!isIsoUtcTimestamp(updatedAt) || !Number.isFinite(now.getTime())) {
    return false;
  }
  return now.getTime() - Date.parse(updatedAt) > STALE_AFTER_MS;
}
