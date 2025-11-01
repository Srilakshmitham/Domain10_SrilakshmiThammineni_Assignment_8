def max_product_subarray(nums):
    max_product = nums[0]
    current_max = nums[0]
    current_min = nums[0]

    for i in range(1, len(nums)):
        if nums[i] < 0:
            current_max, current_min = current_min, current_max
        current_max = max(nums[i], current_max * nums[i])
        current_min = min(nums[i], current_min * nums[i])
        max_product = max(max_product, current_max)

    return max_product

nums = [2, 3, -2, 4]
print("Maximum Subarray Product:", max_product_subarray(nums))
