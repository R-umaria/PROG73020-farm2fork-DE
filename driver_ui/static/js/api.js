const api = {
  async getHealth() {
    const response = await fetch('/api/health');
    return response.json();
  },

  async getDeliveries() {
    const response = await fetch('/api/deliveries/');
    if (!response.ok) throw new Error('Failed to fetch deliveries');
    return response.json();
  },

  async getDrivers() {
    const response = await fetch('/api/drivers/');
    if (!response.ok) throw new Error('Failed to fetch drivers');
    return response.json();
  },

  async getAssignments() {
    const response = await fetch('/api/assignments/');
    if (!response.ok) throw new Error('Failed to fetch assignments');
    return response.json();
  }
};
