"use client";

import { useEffect, useState } from "react";

/** Keeps a section's accordion open the moment it's switched on, while still letting the
 * user collapse/expand it freely afterwards. Replaces `defaultExpanded={included}`, which
 * triggers MUI's "uncontrolled Accordion" warning once `included` changes after mount. */
export function useAutoExpand(included: boolean) {
  const [expanded, setExpanded] = useState(included);

  useEffect(() => {
    if (included) setExpanded(true);
  }, [included]);

  return [expanded, setExpanded] as const;
}
