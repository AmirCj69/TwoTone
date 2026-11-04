// Partner configuration & access control
export const USER_A_ID = 499080623;
export const USER_A_NAME = 'Amir';

export const USER_B_ID = 634034210;
export const USER_B_NAME = 'Ghazal';

export function isAuthorized(userId) {
  if (!userId) return false;
  return userId === USER_A_ID || userId === USER_B_ID;
}

export function getSenderName(userId) {
  if (userId === USER_A_ID) return USER_A_NAME;
  if (userId === USER_B_ID) return USER_B_NAME;
  return 'Someone';
}

export function getPartnerInfo(userId) {
  if (userId === USER_A_ID) {
    return {
      partnerId: USER_B_ID,
      senderName: USER_A_NAME,
      partnerName: USER_B_NAME,
    };
  }
  if (userId === USER_B_ID) {
    return {
      partnerId: USER_A_ID,
      senderName: USER_B_NAME,
      partnerName: USER_A_NAME,
    };
  }
  throw new Error(`Unauthorized user: ${userId}`);
}
