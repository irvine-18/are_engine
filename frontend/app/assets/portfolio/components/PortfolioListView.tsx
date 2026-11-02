import { useState } from "react";
import { Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, Stack, Typography } from "@mui/material";
import FolderIcon from "@mui/icons-material/Folder";
import AddIcon from "@mui/icons-material/Add";

import { PageHeader } from "@/components/layout/PageHeader";
import { PageLoadingOverlay } from "@/components/feedback/PageLoadingOverlay";
import {
  useCreatePortfolio,
  useDeletePortfolio,
  useDuplicatePortfolio,
  usePortfolioList,
  useRenamePortfolio,
} from "@/lib/api/hooks";
import { toPortfolioSummary } from "@/lib/api/portfolioAdapters";
import type { PortfolioSummary } from "@/lib/sampleData/portfolio";
import { PortfolioListCard } from "./PortfolioListCard";
import { PortfolioNameDialog } from "./PortfolioNameDialog";

export function PortfolioListView({ onOpen }: { onOpen: (id: string) => void }) {
  const { data, isLoading, isError } = usePortfolioList();
  const portfolios = (data ?? []).map(toPortfolioSummary);
  const createPortfolio = useCreatePortfolio();
  const renamePortfolio = useRenamePortfolio();
  const duplicatePortfolio = useDuplicatePortfolio();
  const deletePortfolio = useDeletePortfolio();

  const [addOpen, setAddOpen] = useState(false);
  const [renameTarget, setRenameTarget] = useState<PortfolioSummary | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<PortfolioSummary | null>(null);

  return (
    <Stack spacing={2.5}>
      <PageHeader
        section="Asset Market Risk"
        title="Portfolio Construction"
        description="Select or create a new portfolio of assets for SCR market risk calculation."
        icon={<FolderIcon fontSize="small" />}
        statusLabel="Preview"
      />

      {isError ? (
        <Alert severity="error">Couldn&apos;t reach the backend. Is it running? (See backend/README.md.)</Alert>
      ) : (
        <PageLoadingOverlay loading={isLoading} label="Portfolio Construction">
          {portfolios.length === 0 ? (
            <Alert severity="info">No portfolios yet. Create one to get started.</Alert>
          ) : (
            <Stack spacing={1.5}>
              {portfolios.map((p) => (
                <PortfolioListCard
                  key={p.id}
                  portfolio={p}
                  onOpen={() => onOpen(p.id)}
                  onRename={() => setRenameTarget(p)}
                  onDuplicate={() => duplicatePortfolio.mutate(p.id)}
                  onDelete={() => setDeleteTarget(p)}
                />
              ))}
            </Stack>
          )}
        </PageLoadingOverlay>
      )}

      <Box>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setAddOpen(true)}>
          Create portfolio
        </Button>
      </Box>

      <PortfolioNameDialog
        open={addOpen}
        title="Create portfolio"
        onClose={() => setAddOpen(false)}
        onSubmit={(name) => {
          createPortfolio.mutate({ name }, { onSuccess: (created) => onOpen(created.id) });
        }}
      />

      <PortfolioNameDialog
        open={Boolean(renameTarget)}
        title="Rename portfolio"
        initialName={renameTarget?.name}
        onClose={() => setRenameTarget(null)}
        onSubmit={(name) => {
          if (renameTarget) renamePortfolio.mutate({ portfolioId: renameTarget.id, name });
        }}
      />

      <Dialog open={Boolean(deleteTarget)} onClose={() => setDeleteTarget(null)} maxWidth="xs" fullWidth>
        <DialogTitle>Delete portfolio</DialogTitle>
        <DialogContent>
          <Typography variant="body2">
            Delete &quot;{deleteTarget?.name}&quot; and all {deleteTarget?.positionCount ?? 0} of its positions? This
            can&apos;t be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button
            color="error"
            variant="contained"
            onClick={() => {
              if (deleteTarget) deletePortfolio.mutate(deleteTarget.id);
              setDeleteTarget(null);
            }}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}
