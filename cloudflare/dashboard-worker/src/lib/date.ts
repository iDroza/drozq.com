import type { DashboardSnapshot } from "../types";

export const STALE_AFTER_MS = 5 * 60 * 1_000;
export const SEARCH_CONSOLE_TIME_ZONE = "America/Los_Angeles";

interface CalendarDateParts {
  year: number;
  month: number;
  day: number;
}

export function calendarParts(now: Date, timeZone: string): CalendarDateParts {
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

interface ZonedDateTimeParts extends CalendarDateParts {
  hour: number;
  minute: number;
  second: number;
}

function zonedParts(now: Date, timeZone: string): ZonedDateTimeParts {
  if (!Number.isFinite(now.getTime())) {
    throw new RangeError("invalid_date");
  }
  const formatter = new Intl.DateTimeFormat("en-US", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  });
  const values = new Map(
    formatter.formatToParts(now).map((part) => [part.type, part.value]),
  );
  const result = {
    year: Number(values.get("year")),
    month: Number(values.get("month")),
    day: Number(values.get("day")),
    hour: Number(values.get("hour")),
    minute: Number(values.get("minute")),
    second: Number(values.get("second")),
  };
  if (Object.values(result).some((value) => !Number.isInteger(value))) {
    throw new RangeError("invalid_calendar_parts");
  }
  return result;
}

export function localMidnightUtc(
  date: CalendarDateParts,
  timeZone: string,
): Date {
  const target = Date.UTC(date.year, date.month - 1, date.day, 0, 0, 0, 0);
  let candidate = target;
  for (let iteration = 0; iteration < 4; iteration += 1) {
    const represented = zonedParts(new Date(candidate), timeZone);
    const representedAsUtc = Date.UTC(
      represented.year,
      represented.month - 1,
      represented.day,
      represented.hour,
      represented.minute,
      represented.second,
      0,
    );
    const next = candidate + (target - representedAsUtc);
    if (next === candidate) {
      break;
    }
    candidate = next;
  }
  const result = new Date(candidate);
  if (!Number.isFinite(result.getTime())) {
    throw new RangeError("invalid_local_midnight");
  }
  return result;
}

export interface ActivityWindows {
  localDate: string;
  dayStartAt: string;
  monthStartAt: string;
  yearStartAt: string;
  rollingFourWeeksStartAt: string;
  endAt: string;
}

export function getActivityWindows(now: Date, timeZone: string): ActivityWindows {
  const parts = calendarParts(now, timeZone);
  const dayStart = localMidnightUtc(parts, timeZone);
  const monthStart = localMidnightUtc(
    { year: parts.year, month: parts.month, day: 1 },
    timeZone,
  );
  const yearStart = localMidnightUtc(
    { year: parts.year, month: 1, day: 1 },
    timeZone,
  );
  return {
    localDate: isoDate(parts.year, parts.month, parts.day),
    dayStartAt: dayStart.toISOString(),
    monthStartAt: monthStart.toISOString(),
    yearStartAt: yearStart.toISOString(),
    rollingFourWeeksStartAt: new Date(
      now.getTime() - 28 * 24 * 60 * 60 * 1_000,
    ).toISOString(),
    endAt: now.toISOString(),
  };
}

function isoDate(year: number, month: number, day: number): string {
  return `${String(year).padStart(4, "0")}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

export function isIsoCalendarDate(value: unknown): value is string {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/u.test(value)) {
    return false;
  }
  const [year, month, day] = value.split("-").map(Number);
  if (year === undefined || month === undefined || day === undefined) {
    return false;
  }
  const parsed = new Date(Date.UTC(year, month - 1, day, 12, 0, 0, 0));
  return parsed.getUTCFullYear() === year &&
    parsed.getUTCMonth() === month - 1 &&
    parsed.getUTCDate() === day;
}

export function getSearchConsoleThreeMonthPeriod(
  endDate: string,
): DashboardSnapshot["rolling90DayPeriod"] {
  if (!isIsoCalendarDate(endDate)) {
    throw new RangeError("invalid_search_console_end_date");
  }
  const [endYear, endMonth, endDay] = endDate.split("-").map(Number) as [
    number,
    number,
    number,
  ];
  const targetMonthIndex = endYear * 12 + (endMonth - 1) - 3;
  const targetYear = Math.floor(targetMonthIndex / 12);
  const targetMonthIndexInYear = ((targetMonthIndex % 12) + 12) % 12;
  const targetMonth = targetMonthIndexInYear + 1;
  const targetMonthLastDay = new Date(
    Date.UTC(targetYear, targetMonth, 0, 12, 0, 0, 0),
  ).getUTCDate();
  const anchorDay = Math.min(endDay, targetMonthLastDay);
  const start = new Date(
    Date.UTC(targetYear, targetMonth - 1, anchorDay + 1, 12, 0, 0, 0),
  );
  return {
    startDate: isoDate(
      start.getUTCFullYear(),
      start.getUTCMonth() + 1,
      start.getUTCDate(),
    ),
    endDate,
    timeZone: SEARCH_CONSOLE_TIME_ZONE,
  };
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

export function getRollingPeriod(
  now: Date,
  timeZone: string,
  days: number,
): DashboardSnapshot["rolling90DayPeriod"] {
  if (!Number.isSafeInteger(days) || days < 1 || days > 3_660) {
    throw new RangeError("invalid_rolling_days");
  }
  const end = calendarParts(now, timeZone);
  const startDate = new Date(
    Date.UTC(end.year, end.month - 1, end.day - (days - 1), 12, 0, 0, 0),
  );
  return {
    startDate: isoDate(
      startDate.getUTCFullYear(),
      startDate.getUTCMonth() + 1,
      startDate.getUTCDate(),
    ),
    endDate: isoDate(end.year, end.month, end.day),
    timeZone,
  };
}

export function getYearToDatePeriod(
  now: Date,
  timeZone: string,
): DashboardSnapshot["yearToDatePeriod"] {
  const end = calendarParts(now, timeZone);
  return {
    startDate: isoDate(end.year, 1, 1),
    endDate: isoDate(end.year, end.month, end.day),
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

export function isMetricStale(
  updatedAt: string | null,
  now: Date,
  staleAfterMs = STALE_AFTER_MS,
): boolean {
  if (!isIsoUtcTimestamp(updatedAt) || !Number.isFinite(now.getTime())) {
    return false;
  }
  return now.getTime() - Date.parse(updatedAt) > staleAfterMs;
}
