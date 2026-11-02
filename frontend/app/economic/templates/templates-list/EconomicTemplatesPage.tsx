"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { Alert, Button, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle, Snackbar, Stack } from "@mui/material";
import DescriptionOutlinedIcon from "@mui/icons-material/DescriptionOutlined";
import AddIcon from "@mui/icons-material/Add";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";

import { PageHeader } from "@/components/layout/PageHeader";
import { PageLoadingOverlay } from "@/components/feedback/PageLoadingOverlay";
import { EconomicTemplateBuilder } from "../template-builder/EconomicTemplateBuilder";
import { TemplateCard } from "./components/TemplateCard";
import { useEconomicTemplates } from "@/stores/economicTemplates";
import { useCreateEconomicDataTemplate, useEditEconomicDataTemplate, useRunEdeTemplate } from "@/lib/api/hooks";
import { defaultValuationDate, emptyTemplate, type EconomicDataTemplate } from "@/lib/economicTemplates";

type View = { mode: "list" } | { mode: "new" } | { mode: "edit"; id: string };

export function EconomicTemplatesPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const { templates, isLoading, addTemplate, updateTemplate, removeTemplate, setDefaultTemplate } = useEconomicTemplates();
  const [view, setView] = useState<View>(searchParams.get("action") === "new" ? { mode: "new" } : { mode: "list" });
  const [snackbar, setSnackbar] = useState<string | null>(null);
  const [successRun, setSuccessRun] = useState<{ id: string; name: string; saved: boolean } | null>(null);
  const runTemplate = useRunEdeTemplate();
  const createMutation = useCreateEconomicDataTemplate();
  const editMutation = useEditEconomicDataTemplate();

  // "View" leads to the Curves/Inflation page (see EconomicDataPage) showing the
  // template's actual run output, not a read-only copy of the builder -- so it also
  // needs to become the default template those pages read from.
  function handleView(template: EconomicDataTemplate) {
    setDefaultTemplate(template.id, true);
    router.push("/economic/curves");
  }

  function handleRun(template: EconomicDataTemplate) {
    runTemplate.mutate(template.id, {
      onSuccess: () => {
        setDefaultTemplate(template.id, true);
        setSuccessRun({ id: template.id, name: template.name, saved: false });
      },
      onError: (err) => setSnackbar(`Couldn't run "${template.name}": ${(err as Error).message}`),
    });
  }

  function handleSave(template: EconomicDataTemplate) {
    if (view.mode === "edit") {
      updateTemplate(template.id, template);
      setSnackbar(`Updated "${template.name}"`);
    } else {
      addTemplate(template);
      setSnackbar(`Saved "${template.name}"`);
    }
    setView({ mode: "list" });
  }

  /** Saves the template (create or update, awaiting the server's own copy rather
   * than the optimistic-update path `handleSave` uses, since the run below needs a
   * confirmed id/doc in Cosmos to read back), then runs it -- only once the run
   * itself succeeds does this leave the builder and show the success dialog, so a
   * failure at either step leaves the user in the builder with their edits intact. */
  async function handleSaveAndRun(template: EconomicDataTemplate) {
    try {
      const saved =
        view.mode === "edit"
          ? await editMutation.mutateAsync({ id: template.id, template })
          : await createMutation.mutateAsync(template);
      await runTemplate.mutateAsync(saved.id);
      setDefaultTemplate(saved.id, true);
      setView({ mode: "list" });
      setSuccessRun({ id: saved.id, name: saved.name, saved: true });
    } catch (err) {
      setSnackbar(`Couldn't save & run "${template.name}": ${(err as Error).message}`);
    }
  }

  function handleBackToTemplatesFromDialog() {
    queryClient.invalidateQueries({ queryKey: ["economic-data-templates"] });
    setSuccessRun(null);
  }

  function handleViewCurvesFromDialog() {
    setSuccessRun(null);
    router.push("/economic/curves");
  }

  function handleDuplicate(source: EconomicDataTemplate) {
    addTemplate({
      ...source,
      id: `template-${Date.now()}`,
      name: `${source.name} (copy)`,
      createdAt: new Date().toISOString(),
      isDefault: false,
    });
  }

  if (view.mode === "new" || view.mode === "edit") {
    const initial =
      view.mode === "new" ? emptyTemplate(defaultValuationDate()) : templates.find((t) => t.id === view.id) ?? emptyTemplate(defaultValuationDate());
    const titles = { new: "New economic data template", edit: "Edit economic data template" };
    return (
      <Stack spacing={2.5}>
        <PageHeader
          section="Economic Engine"
          title={titles[view.mode]}
          description="Bundle interest, inflation, HICP and equity-adjustment inputs into a reusable, named template for Asset Market Risk runs."
          icon={<DescriptionOutlinedIcon fontSize="small" />}
        />
        <EconomicTemplateBuilder
          initial={initial}
          onSave={handleSave}
          onSaveAndRun={handleSaveAndRun}
          onCancel={() => setView({ mode: "list" })}
          isSavingAndRunning={createMutation.isPending || editMutation.isPending || runTemplate.isPending}
        />
      </Stack>
    );
  }

  return (
    <Stack spacing={2.5}>
      <PageHeader
        section="Economic Engine"
        title="Economic Data Templates"
        description="Select or create a bundle of interest, inflation, HICP and equity-adjustment inputs to use as the economic basis."
        icon={<DescriptionOutlinedIcon fontSize="small" />}
        actions={
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setView({ mode: "new" })}>
            New template
          </Button>
        }
      />

      <PageLoadingOverlay loading={isLoading} label="Templates">
        {templates.length === 0 ? (
          <Alert severity="info">
            No templates saved yet. Create one to use as the economic data basis for Single Asset or Portfolio runs.
          </Alert>
        ) : (
          <Stack spacing={1.5}>
            {templates.map((t) => (
              <TemplateCard
                key={t.id}
                template={t}
                onUse={(checked) => setDefaultTemplate(t.id, checked)}
                onView={() => handleView(t)}
                onEdit={() => setView({ mode: "edit", id: t.id })}
                onDuplicate={() => handleDuplicate(t)}
                onDelete={() => removeTemplate(t.id)}
                onRun={() => handleRun(t)}
                isRunning={runTemplate.isPending && runTemplate.variables === t.id}
              />
            ))}
          </Stack>
        )}
      </PageLoadingOverlay>

      <Snackbar open={Boolean(snackbar)} autoHideDuration={4000} onClose={() => setSnackbar(null)} message={snackbar} />

      <Dialog open={Boolean(successRun)} onClose={handleBackToTemplatesFromDialog}>
        <DialogTitle>
          <Stack direction="row" spacing={1} alignItems="center">
            <CheckCircleIcon color="success" fontSize="small" />
            <span>{successRun?.saved ? "Template saved and run successfully" : "Template run successfully"}</span>
          </Stack>
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            {successRun?.saved
              ? `"${successRun?.name}" was saved and its economic data engine ran successfully`
              : `"${successRun?.name}"'s economic data engine ran successfully`}{" "}
            — see it in Curves and Inflation.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleBackToTemplatesFromDialog}>Back to Templates</Button>
          <Button variant="contained" onClick={handleViewCurvesFromDialog}>
            View Curves
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}
