"use client";

import { useQueryClient } from "@tanstack/react-query";

import {
  useCreateEconomicDataTemplate,
  useDeleteEconomicDataTemplate,
  useEconomicDataTemplates,
  useEditEconomicDataTemplate,
} from "@/lib/api/hooks";
import type { EconomicDataTemplate } from "@/lib/economicTemplates";

const TEMPLATES_QUERY_KEY = ["economic-data-templates"];

export function useEconomicTemplates() {
  const { data, isLoading } = useEconomicDataTemplates();
  const queryClient = useQueryClient();
  const createMutation = useCreateEconomicDataTemplate();
  const editMutation = useEditEconomicDataTemplate();
  const deleteMutation = useDeleteEconomicDataTemplate();

  const templates = data ?? [];
  const activeTemplate = templates.find((t) => t.isDefault);

  function addTemplate(template: EconomicDataTemplate) {
    queryClient.setQueryData<EconomicDataTemplate[]>(TEMPLATES_QUERY_KEY, (prev) => [...(prev ?? []), template]);
    createMutation.mutate(template);
  }

  function updateTemplate(id: string, patch: Partial<EconomicDataTemplate>) {
    let merged: EconomicDataTemplate | undefined;
    queryClient.setQueryData<EconomicDataTemplate[]>(TEMPLATES_QUERY_KEY, (prev) =>
      (prev ?? []).map((t) => {
        if (t.id !== id) return t;
        merged = { ...t, ...patch };
        return merged;
      }),
    );
    if (merged) editMutation.mutate({ id, template: merged });
  }

  function removeTemplate(id: string) {
    queryClient.setQueryData<EconomicDataTemplate[]>(TEMPLATES_QUERY_KEY, (prev) => (prev ?? []).filter((t) => t.id !== id));
    deleteMutation.mutate(id);
  }

  function setDefaultTemplate(id: string, isDefault: boolean) {
    for (const t of templates) {
      if (t.id === id) {
        if (t.isDefault !== isDefault) updateTemplate(t.id, { isDefault });
      } else if (isDefault && t.isDefault) {
        updateTemplate(t.id, { isDefault: false });
      }
    }
  }

  return { templates, activeTemplate, isLoading, addTemplate, updateTemplate, removeTemplate, setDefaultTemplate };
}
