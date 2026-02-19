/**
 * Add two numbers together.
 * @param a - First operand
 * @param b - Second operand
 * @returns The sum of a and b
 */
export function add(a: number, b: number): number {
  return a + b;
}

/**
 * Divide a by b with zero-check.
 * @throws Error if b is zero
 */
export function divide(a: number, b: number): number {
  if (b === 0) throw new Error("Division by zero");
  return a / b;
}

export class Calculator {
  private history: number[] = [];

  add(a: number, b: number): number {
    const result = a + b;
    this.history.push(result);
    return result;
  }
}

export type Operation = "add" | "subtract" | "multiply" | "divide";

export interface CalculatorConfig {
  precision: number;
  strict: boolean;
}
