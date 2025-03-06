/**
 * Utility functions for working with Tableau Extensions API
 */

/**
 * Fetches data from the specified worksheet
 * @param {Object} worksheet - Tableau worksheet object
 * @param {boolean} includeAllColumns - Whether to include all columns or just those in the view
 * @returns {Promise<Object>} - Formatted data object
 */
export const getWorksheetData = async (worksheet, includeAllColumns = true) => {
  try {
    // Get the summary data (includes all columns shown in the view)
    const summaryDataOptions = {
      ignoreSelection: false,
      includeAllColumns: includeAllColumns,
      maxRows: 10000 // Set a reasonable limit to avoid performance issues
    };
    
    const dataTable = await worksheet.getSummaryDataAsync(summaryDataOptions);
    
    // Format the data in a more friendly structure
    const data = {
      sheetName: worksheet.name,
      columns: dataTable.columns.map(column => ({
        fieldName: column.fieldName,
        dataType: column.dataType,
        isReferenced: column.isReferenced
      })),
      rows: []
    };
    
    // Process each row
    for (let i = 0; i < dataTable.totalRowCount; i++) {
      const row = {};
      for (let j = 0; j < dataTable.columns.length; j++) {
        const column = dataTable.columns[j];
        row[column.fieldName] = dataTable.data[i][j].value;
      }
      data.rows.push(row);
    }
    
    return data;
  } catch (error) {
    console.error('Error fetching worksheet data:', error);
    throw error;
  }
};

/**
 * Gets information about all fields in a worksheet
 * @param {Object} worksheet - Tableau worksheet object
 * @returns {Promise<Array>} - Array of field information
 */
export const getFieldInfo = async (worksheet) => {
  try {
    // Get all fields from the worksheet
    const fields = await worksheet.getFieldsAsync();
    
    // Format the fields information
    return fields.map(field => ({
      name: field.name,
      fieldType: field.fieldType,
      dataType: field.dataType,
      isHidden: field.isHidden,
      isGenerated: field.isGenerated,
      isCalculatedField: field.isCalculatedField
    }));
  } catch (error) {
    console.error('Error fetching field information:', error);
    throw error;
  }
};

/**
 * Gets all worksheets from the current dashboard
 * @returns {Array} - Array of Tableau worksheet objects
 */
export const getAllWorksheets = () => {
  try {
    const dashboard = window.tableau.extensions.dashboardContent.dashboard;
    return dashboard.worksheets;
  } catch (error) {
    console.error('Error getting worksheets:', error);
    return [];
  }
};

/**
 * Gets the selected marks from a worksheet
 * @param {Object} worksheet - Tableau worksheet object
 * @returns {Promise<Object>} - Selected marks data
 */
export const getSelectedMarks = async (worksheet) => {
  try {
    const marksInfo = await worksheet.getSelectedMarksAsync();
    
    // Format the selected marks data
    const data = {
      sheetName: worksheet.name,
      marksCount: marksInfo.data.length,
      columns: marksInfo.columns.map(column => ({
        fieldName: column.fieldName,
        dataType: column.dataType
      })),
      marks: []
    };
    
    // Process each mark
    for (let i = 0; i < marksInfo.data.length; i++) {
      const mark = {};
      for (let j = 0; j < marksInfo.columns.length; j++) {
        const column = marksInfo.columns[j];
        mark[column.fieldName] = marksInfo.data[i][j].value;
      }
      data.marks.push(mark);
    }
    
    return data;
  } catch (error) {
    console.error('Error fetching selected marks:', error);
    throw error;
  }
};