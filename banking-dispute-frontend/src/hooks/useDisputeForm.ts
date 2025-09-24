import { useState } from "react";
import type { DisputeForm } from "../types/index";
import { disputeApi } from "../services/disputeApis";
import { generateDisputeId, calculatePriority } from "../utils/chatHelpers";
import type { DisputeApiResponse } from "../types/types";

export const useDisputeForm = () => {
  const [disputeForm, setDisputeForm] = useState<DisputeForm>({});
  const [isLoading, setIsLoading] = useState(false);

  const updateForm = (field: keyof DisputeForm, value: any) => {
    setDisputeForm((prev) => ({ ...prev, [field]: value }));
  };

  const createDispute = async (): Promise<string> => {
    setIsLoading(true);
    try {
      const disputeId = generateDisputeId();
      const priority = calculatePriority(disputeForm.amount);

      const disputePayload: DisputeForm = {
        ...disputeForm,
        priority,
      };

      await disputeApi.create(disputePayload);

      return disputeId;
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const getDisputeById = async (disputeId: string) : Promise<DisputeApiResponse> => {
    setIsLoading(true);
    try {
      const getDisputeResponse = await disputeApi.track(disputeId);
      return getDisputeResponse;
    } catch (err) {
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setDisputeForm({});
  };

  return {
    disputeForm,
    isLoading,
    updateForm,
    createDispute,
    getDisputeById,
    resetForm,
  };
};
