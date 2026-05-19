import { describe, it, expect, beforeEach } from "vitest";
import { buildApiUrl } from "../lib/api";
import { getAuthToken, setAuthToken, clearAuthToken } from "../lib/auth";

describe("buildApiUrl", () => {
  it("appends path to the base URL without double slashes", () => {
    const url = buildApiUrl("/login");
    expect(url).toMatch(/\/login$/);
    expect(url).not.toContain("//login");
  });

  it("handles paths without a leading slash", () => {
    const url = buildApiUrl("predict");
    expect(url).toMatch(/\/predict$/);
  });

  it("strips a trailing slash from the base before joining", () => {
    const url1 = buildApiUrl("/healthz");
    const url2 = buildApiUrl("healthz");
    expect(url1).toBe(url2);
  });
});

describe("auth utilities", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("returns null when no token has been stored", () => {
    expect(getAuthToken()).toBeNull();
  });

  it("stores and retrieves a token", () => {
    setAuthToken("test-jwt-token-abc123");
    expect(getAuthToken()).toBe("test-jwt-token-abc123");
  });

  it("overwrites an existing token", () => {
    setAuthToken("first-token");
    setAuthToken("second-token");
    expect(getAuthToken()).toBe("second-token");
  });

  it("clears the stored token", () => {
    setAuthToken("test-jwt-token-abc123");
    clearAuthToken();
    expect(getAuthToken()).toBeNull();
  });
});
