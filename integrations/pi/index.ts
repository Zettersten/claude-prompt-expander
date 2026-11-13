import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { filterPayload } from "../provider-filter";

export default function (pi: ExtensionAPI) {
  pi.on("before_provider_request", (event) => {
    return JSON.parse(filterPayload(JSON.stringify(event.payload)));
  });
}
