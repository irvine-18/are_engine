import { Suspense } from "react";

import { ResultsPage } from "./ResultsPage";

export default function Page() {
  return (
    <Suspense>
      <ResultsPage />
    </Suspense>
  );
}
