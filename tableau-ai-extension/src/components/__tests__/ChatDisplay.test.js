import React from 'react';
import { render, screen } from '@testing-library/react';
import ChatDisplay from '../ChatDisplay';

describe('ChatDisplay', () => {
  test('renders a response string correctly', () => {
    // Mock props
    const testResponse = 'This is a test response from the AI assistant';
    
    // Render the component with the mock props
    render(<ChatDisplay response={testResponse} />);
    
    // Check that the response text appears in the DOM
    const responseElement = screen.getByText(testResponse);
    expect(responseElement).toBeInTheDocument();
    
    // Verify the response is contained within the expected container
    const responseContainer = responseElement.closest('.response-container');
    expect(responseContainer).toBeInTheDocument();
  });
});