import { useState } from "react";
import { Button, Dialog, DialogActions, DialogContent, DialogTitle, TextField } from "@mui/material";

interface PortfolioNameDialogProps {
  open: boolean;
  title: string;
  initialName?: string;
  onClose: () => void;
  onSubmit: (name: string) => void;
}

export function PortfolioNameDialog({ open, title, initialName, onClose, onSubmit }: PortfolioNameDialogProps) {
  const [name, setName] = useState(initialName ?? "");

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="xs"
      fullWidth
      TransitionProps={{ onEnter: () => setName(initialName ?? "") }}
    >
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <TextField
          autoFocus
          fullWidth
          label="Portfolio name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          sx={{ mt: 1 }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && name.trim()) {
              onSubmit(name.trim());
              onClose();
            }
          }}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          disabled={!name.trim()}
          onClick={() => {
            onSubmit(name.trim());
            onClose();
          }}
        >
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
}
