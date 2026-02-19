package calculator

// Add returns the sum of two integers.
// It handles overflow by wrapping.
func Add(a, b int) int {
	return a + b
}

// Divide returns a/b. Returns error if b is zero.
func Divide(a, b int) (int, error) {
	if b == 0 {
		return 0, fmt.Errorf("division by zero")
	}
	return a / b, nil
}

// Calculator holds state for chained operations.
type Calculator struct {
	Result int
}

func internal() {}
