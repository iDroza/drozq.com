export const MAX_COUNT = 1_000_000_000;
export const MAX_SPEND_USD = 1_000_000_000_000;

export function isFiniteNonnegative(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value) && value >= 0;
}

export function requireCount(value: unknown, label: string): number {
  let parsed: number;
  if (typeof value === "number") {
    parsed = value;
  } else if (typeof value === "string" && /^\d+$/.test(value.trim())) {
    parsed = Number(value.trim());
  } else {
    throw new RangeError(`${label}_invalid`);
  }

  if (
    !Number.isSafeInteger(parsed) ||
    parsed < 0 ||
    parsed > MAX_COUNT
  ) {
    throw new RangeError(`${label}_invalid`);
  }
  return parsed;
}

export function requireNonnegativeNumber(value: unknown, label: string): number {
  let parsed: number;
  if (typeof value === "number") {
    parsed = value;
  } else if (typeof value === "string" && value.trim() !== "") {
    parsed = Number(value);
  } else {
    throw new RangeError(`${label}_invalid`);
  }

  if (!Number.isFinite(parsed) || parsed < 0 || parsed > MAX_COUNT) {
    throw new RangeError(`${label}_invalid`);
  }
  return parsed;
}

export function requireSpend(value: number): number {
  if (!Number.isFinite(value) || value < 0 || value > MAX_SPEND_USD) {
    throw new RangeError("spend_invalid");
  }
  return value;
}
