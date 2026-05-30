export class CalculusSolver {
  constructor({ endpoint }) {
    if (!endpoint) {
      throw new Error("CalculusSolver requires an endpoint URL.");
    }
    this.endpoint = endpoint;
  }

  async _fetch(url, requestInit) {
    if (typeof fetch !== "undefined") {
      return fetch(url, requestInit);
    }
    const nodeFetch = await import("node-fetch");
    return nodeFetch.default(url, requestInit);
  }

  async solve(input) {
    const response = await this._fetch(this.endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(input),
    });

    if (!response.ok) {
      const message = await response.text();
      throw new Error(
        `CalculusSolver request failed: ${response.status} ${message}`,
      );
    }

    return response.json();
  }
}
