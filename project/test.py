import numpy as np

def annual_return(start_value, end_value, years):
    """
    Calculate the annual return given the starting and ending investment values and the number of years.

    Args:
        start_value (float): The initial value of the investment.
        end_value (float): The final value of the investment.
        years (float): The number of years the investment was held.

    Returns:
        float: The annual return as a decimal.
    """
    return (end_value / start_value) ** (1/years) - 1

start_value = 2000000
end_value = 10000000
years = 10 # 假設投資期為1年

annual_rate = annual_return(start_value, end_value, years)

print(f"年報酬率為：{annual_rate * 100}%")



