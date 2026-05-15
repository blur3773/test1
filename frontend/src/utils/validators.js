export const normalizePhoneDigits = (value = "") => String(value).replace(/\D/g, "");

export const isValidEmail = (value = "") => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value).trim());

export const isValidRuPhone = (value = "") => {
  const digits = normalizePhoneDigits(value);
  if (!digits) {
    return false;
  }
  if (digits.length === 11) {
    return digits.startsWith("7") || digits.startsWith("8");
  }
  return digits.length === 10;
};

export const isValidRuPhoneWithRequiredPrefix = (value = "") => {
  const normalizedValue = String(value).trim();
  const digits = normalizePhoneDigits(normalizedValue);
  if (normalizedValue.startsWith("+7")) {
    return digits.length === 11 && digits.startsWith("7");
  }
  return digits.length === 11 && (digits.startsWith("7") || digits.startsWith("8"));
};

export const formatRuPhoneForStore = (value = "") => {
  const digits = normalizePhoneDigits(value);
  if (digits.length === 11 && digits.startsWith("8")) {
    return `+7${digits.slice(1)}`;
  }
  if (digits.length === 11 && digits.startsWith("7")) {
    return `+${digits}`;
  }
  if (digits.length === 10) {
    return `+7${digits}`;
  }
  return value.trim();
};
