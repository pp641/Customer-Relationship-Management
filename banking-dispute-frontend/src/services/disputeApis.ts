import axios from 'axios';
import type { DisputeForm } from '../types/index';
import  { BASE_URL } from '../Constants/index';

export const disputeApi = {
  create: async (disputeData: DisputeForm): Promise<DisputeForm> => {
    try {
      const response = await axios.post<DisputeForm>(
        `${BASE_URL}/dispute`,
        disputeData,
        {
          headers: { 'Content-Type': 'application/json' },
          timeout: 5000,
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to create dispute:', error);
      throw new Error('Failed to create dispute. Please try again.');
    }
  },

  track: async (disputeId: string): Promise<any> => {
    try {
      const response = await axios.get(`${BASE_URL}/dispute/${disputeId}`, {
        headers: { 'Accept': 'application/json' },
        timeout: 5000,
      });

      if (response.data) {
        return response.data; 
      } else {
        throw new Error(`No dispute found for ID: ${disputeId}. Please enter a valid ID.`);
      }
    } catch (error: any) {
      if (error.response?.status === 404) {
        throw new Error(`No dispute found for ID: ${disputeId}. Please enter a valid ID.`);
      }
      console.error('Failed to track dispute:', error);
      throw new Error('Failed to track dispute. Please try again.');
    }
  }
};