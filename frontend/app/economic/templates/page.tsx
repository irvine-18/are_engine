import { Suspense } from "react";

import { EconomicTemplatesPage } from "./templates-list/EconomicTemplatesPage";

export default function Page() {
  return (
    <Suspense>
      <EconomicTemplatesPage />
    </Suspense>
  );
}
