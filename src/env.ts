import { defineEnvVars } from "@sveltejs/kit/env";
import * as z from "zod";

export const variables = defineEnvVars({
  DATABASE_URL: {
    description: "PostgreSQL connection string.",
    schema: z.url({ protocol: /^postgres(ql)?$/ })
  }
});
