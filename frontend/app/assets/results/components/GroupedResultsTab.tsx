import { useState } from "react";
import { Stack, Tab, Tabs } from "@mui/material";

import { GroupedTable } from "./GroupedTable";
import { GROUP_DIMENSIONS, groupResults } from "../utils/groupResults";
import type { EnrichedPositionResult } from "../utils/joinResults";

interface GroupedResultsTabProps {
  rows: EnrichedPositionResult[];
  onDrill: (group: string) => void;
}

export function GroupedResultsTab({ rows, onDrill }: GroupedResultsTabProps) {
  const [sub, setSub] = useState(0);
  const grouped = groupResults(rows, GROUP_DIMENSIONS[sub].keyOf);

  return (
    <Stack spacing={2}>
      <Tabs value={sub} onChange={(_, v) => setSub(v)}>
        {GROUP_DIMENSIONS.map((g) => (
          <Tab key={g.label} label={g.label} />
        ))}
      </Tabs>
      <GroupedTable rows={grouped} onDrill={onDrill} />
    </Stack>
  );
}
