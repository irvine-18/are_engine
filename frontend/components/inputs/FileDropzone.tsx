"use client";

import { useCallback, useRef, useState } from "react";
import { Box, Paper, Stack, Typography } from "@mui/material";
import UploadFileIcon from "@mui/icons-material/UploadFile";

interface FileDropzoneProps {
  accept?: string;
  onFile: (file: File) => void;
}

export function FileDropzone({ accept = ".xlsx,.csv", onFile }: FileDropzoneProps) {
  const [fileName, setFileName] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(
    (files: FileList | null) => {
      const file = files?.[0];
      if (!file) return;
      setFileName(`${file.name} (${(file.size / 1024).toFixed(0)} KB)`);
      onFile(file);
    },
    [onFile],
  );

  return (
    <Paper
      variant="outlined"
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        handleFiles(e.dataTransfer.files);
      }}
      sx={{
        p: 4,
        textAlign: "center",
        cursor: "pointer",
        borderStyle: "dashed",
        borderColor: dragging ? "primary.main" : "divider",
        bgcolor: dragging ? "action.hover" : "transparent",
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        hidden
        onChange={(e) => handleFiles(e.target.files)}
        aria-label="Upload file"
      />
      <Stack spacing={1} alignItems="center">
        <UploadFileIcon color="action" />
        <Typography variant="body2">Drag and drop a {accept} file here, or click to browse</Typography>
        {fileName && (
          <Box>
            <Typography variant="caption" color="text.secondary">
              {fileName}
            </Typography>
          </Box>
        )}
      </Stack>
    </Paper>
  );
}
