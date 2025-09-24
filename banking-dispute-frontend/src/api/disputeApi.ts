import axios from 'axios';
import { BASE_URL } from '../Constants/constants';
import type { DisputeForm  } from '../types/types';

export const createDisputeApi = async (dispute: DisputeForm) => {
  const response = await axios.post<DisputeForm>(
    `${BASE_URL}/dispute`,
    dispute,
    {
      headers: { 'Content-Type': 'application/json' },
      timeout: 5000,
    }
  );
  return response.data;
};
