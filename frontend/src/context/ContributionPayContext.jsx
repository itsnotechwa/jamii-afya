import { createContext, useContext } from 'react';

const ContributionPayContext = createContext({
  openPayModal: () => {},
});

export function useContributionPay() {
  return useContext(ContributionPayContext);
}

export { ContributionPayContext };
