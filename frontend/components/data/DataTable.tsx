"use client";

import { useMemo } from "react";
import { Button } from "@mui/material";
import FileDownloadIcon from "@mui/icons-material/FileDownload";
import {
  DataGrid,
  GridToolbarContainer,
  GridToolbarQuickFilter,
  GridToolbarColumnsButton,
  GridToolbarFilterButton,
  type GridColDef,
} from "@mui/x-data-grid";
import * as XLSX from "xlsx";

interface DataTableProps<T extends { id: string | number }> {
  rows: T[];
  columns: GridColDef[];
  fileName?: string;
  height?: number;
  loading?: boolean;
}

function Toolbar({ rows, fileName }: { rows: Record<string, unknown>[]; fileName: string }) {
  const exportXlsx = () => {
    const sheet = XLSX.utils.json_to_sheet(rows);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, sheet, "Data");
    XLSX.writeFile(workbook, `${fileName}.xlsx`);
  };

  return (
    <GridToolbarContainer>
      <GridToolbarColumnsButton />
      <GridToolbarFilterButton />
      <Button size="small" startIcon={<FileDownloadIcon />} onClick={exportXlsx}>
        Export XLSX
      </Button>
      <GridToolbarQuickFilter sx={{ ml: "auto" }} />
    </GridToolbarContainer>
  );
}

export function DataTable<T extends { id: string | number }>({
  rows,
  columns,
  fileName = "export",
  height = 480,
  loading = false,
}: DataTableProps<T>) {
  const columnsWithDefaults = useMemo(
    () => columns.map((c) => ({ ...c, align: c.type === "number" ? "right" : c.align, headerAlign: c.type === "number" ? "right" : c.headerAlign })),
    [columns],
  );

  return (
    <div style={{ height, width: "100%" }}>
      <DataGrid
        rows={rows}
        columns={columnsWithDefaults}
        density="compact"
        loading={loading}
        slots={{ toolbar: () => <Toolbar rows={rows as unknown as Record<string, unknown>[]} fileName={fileName} /> }}
        initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
        pageSizeOptions={[25, 50, 100]}
        sx={{
          "& .MuiDataGrid-cell--textRight.negative": { color: "error.main" },
        }}
      />
    </div>
  );
}
