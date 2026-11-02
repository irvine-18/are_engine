import { Button } from "@mui/material";

import { DataTable } from "@/components/data/DataTable";
import { fmtMoney } from "@/lib/format";
import type { GroupedRow } from "../utils/groupResults";

interface GroupedTableProps {
  rows: GroupedRow[];
  onDrill: (group: string) => void;
}

export function GroupedTable({ rows, onDrill }: GroupedTableProps) {
  return (
    <DataTable
      height={420}
      fileName="scr-by-group"
      rows={rows}
      columns={[
        {
          field: "group",
          headerName: "Group",
          flex: 1,
          minWidth: 180,
          renderCell: (p) => (
            <Button size="small" onClick={() => onDrill(p.value as string)} sx={{ fontWeight: 600, justifyContent: "flex-start" }}>
              {p.value}
            </Button>
          ),
        },
        { field: "positionCount", headerName: "Positions", type: "number", width: 100 },
        { field: "marketValue", headerName: "MV", type: "number", width: 140, valueFormatter: (v) => fmtMoney(v as number, undefined, true) },
        { field: "scrInterestUp", headerName: "SCR Interest (Up)", type: "number", width: 150, valueFormatter: (v) => fmtMoney(v as number, undefined, true) },
        { field: "scrInterestDown", headerName: "SCR Interest (Down)", type: "number", width: 150, valueFormatter: (v) => fmtMoney(v as number, undefined, true) },
        { field: "scrSpread", headerName: "SCR Spread", type: "number", width: 130, valueFormatter: (v) => fmtMoney(v as number, undefined, true) },
        { field: "scrEquity", headerName: "SCR Equity", type: "number", width: 130, valueFormatter: (v) => fmtMoney(v as number, undefined, true) },
        { field: "scrTotal", headerName: "SCR Total", type: "number", width: 130, valueFormatter: (v) => fmtMoney(v as number, undefined, true) },
      ]}
    />
  );
}
