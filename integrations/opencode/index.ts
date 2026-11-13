import { Plugin } from "@opencode/plugin";
import { filterPayload } from "../provider-filter";

export default Plugin.define({
  id: "prompt-abbreviation-expander",
  async setup(ctx) {
    await ctx.session.hook("http.request", async (event) => {
      const request = event.request;
      if (request.body === null) return;

      const encoding = request.headers.get("content-encoding");
      if (encoding && encoding.toLowerCase() !== "identity") {
        throw new Error("Abbreviation filtering requires uncompressed JSON");
      }

      const body = filterPayload(new Uint8Array(await request.clone().arrayBuffer()));
      const headers = new Headers(request.headers);
      headers.delete("content-length");
      event.request = new Request(request, { headers, body });
    });
  },
});
