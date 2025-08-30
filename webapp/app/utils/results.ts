export type ResultOk<T> = {
  errors: null;
  value: T;
};
export type ResultError<E> = {
  errors: E[];
  value: null;
};
export type Result<T, E> = ResultOk<T> | ResultError<E>;

export const ok = <T>(value: T): ResultOk<T> => ({
  errors: null,
  value,
});

export const error = <E>(...errors: E[]): ResultError<E> => ({
  errors,
  value: null,
});

/**
 * Takes an array of results and returns a single result.
 * If any of the input results is an error, the returned result contains a merged array of all
 * encountered errors.
 * If all input results are ok, the `value` in the returned result is an array of all `value` fields
 * in the input list.
 */
export const collectResultArray = <T, E>(results: Result<T, E>[]): Result<T[], E> => {
  // The result is ok until any error is found
  let collectResult: Result<T[], E> = {
    errors: null,
    value: [],
  };
  results.forEach((result) => {
    if (result.errors !== null) {
      if (collectResult.errors === null) collectResult = {
        errors: [],
        value: null,
      };
      collectResult.errors.push(...result.errors);
    } else if (collectResult.errors === null) {
      collectResult.value.push(result.value);
    }
  });
  return collectResult;
};
